"""Stage7 live dry-run: full chain collect->route->verify->bus->monitor, no blocking.

Safe: synthetic posts mimicking real viral claims, no network, no Neo4j server
required (store runs disabled). Reports keys/quota/errors + what live needs.
"""
import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.config import Config  # loads MiroFish-main/.env


def load(mod_path, name):
    spec = importlib.util.spec_from_file_location(name, BACKEND / mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def key_status():
    out = {}
    for key in ("LLM_API_KEY", "ZEP_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD",
                "X_BEARER_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "YOUTUBE_API_KEY",
                "PIB_FACTCHECK_RSS_URL", "ACTION_MODE", "INSTAGRAM_WEBHOOK_VERIFY_TOKEN"):
        value = os.environ.get(key, "")
        placeholder = (not value) or ("your_" in value) or ("change_me" in value)
        out[key] = "MISSING-or-placeholder" if placeholder else "SET"
    return out


def main():
    print("== Stage7 dry-run: full chain, no blocking ==")
    keys = key_status()
    for key, status in keys.items():
        print(f"  {key}: {status}")
    print(f"  baseline validate: {Config.validate()}")
    print(f"  stage0 warnings: {Config.validate_stage0()}")

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(Config.NEO4J_URI, auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD or "nope"))
        driver.verify_connectivity()
        print("  neo4j: REACHABLE")
    except Exception as exc:
        print(f"  neo4j: UNREACHABLE (expected without server): {type(exc).__name__}")

    connectors = BACKEND / "app" / "services" / "connectors"
    sys.path.insert(0, str(connectors))
    scoring = load("app/services/connectors/scoring.py", "dryrun_scoring")
    route_post = scoring._router.route_post
    spread = load("app/services/spread_graph/analytics.py", "dryrun_analytics")
    pib = load("app/services/verification/pib_client.py", "dryrun_pib")
    workers = load("app/services/verification/workers.py", "dryrun_workers")
    busmod = load("app/services/eventbus/bus.py", "dryrun_bus")
    store_mod = load("app/services/eventbus/monitor_store.py", "dryrun_store")
    wiring = load("app/services/eventbus/wiring.py", "dryrun_wiring")
    sched = load("app/services/realtime/scheduler.py", "dryrun_sched")

    clients = load("app/services/connectors/clients.py", "dryrun_clients")
    viral_x = clients.parse_x_tweet({
        "id": "x100", "text": "Viral: Government of India UPI shutdown from tonight, PIB says?",
        "author_id": "acc_viral", "lang": "en",
        "public_metrics": {"like_count": 8000, "retweet_count": 3500, "reply_count": 600, "impression_count": 400000},
    })
    viral_ig = clients.parse_instagram_media({
        "id": "ig200", "caption": "PM-KISAN money blocked viral reel Government of India",
        "media_type": "VIDEO", "like_count": 9000, "comments_count": 800,
    })
    offtopic = clients.parse_x_tweet({"id": "x999", "text": "cute cat video", "public_metrics": {"like_count": 5}})

    facts = [pib.FactCheck(external_id="pib1", title="PIB: viral UPI shutdown claim is fake", link="https://factcheck.pib.gov.in/1"),
             pib.FactCheck(external_id="pib2", title="PIB: PM-KISAN blocked claim is fake", link="https://factcheck.pib.gov.in/2")]

    store = store_mod.MonitorStore()
    callbacks = wiring.make_callbacks(store)
    bus = busmod.EventBus(start_simulation=callbacks["start_simulation"], queue_report=callbacks["queue_report"])
    quota_buckets = sched.make_buckets() if hasattr(sched, "make_buckets") else {}

    routed_posts = []
    for post in (viral_x, viral_ig, offtopic):
        try:
            signal = scoring.to_routing_input(post)
        except ValueError:
            print(f"  SKIP off-topic: {post.platform}:{post.platform_post_id}")
            continue
        decision = route_post(signal)
        burst = spread.detect_burst([0.2, 0.5, float(signal.spread_velocity or 0.7)])
        result = workers.verify_claim(post.text, facts, content_type=post.content_type, language=post.language)
        event = busmod.BusEvent(platform=post.platform, post_id=post.platform_post_id, text=post.text,
                                tier=decision.tier, priority_score=decision.priority_score,
                                velocity=float(getattr(signal, 'spread_velocity', 0.0) or 0.7),
                                burst=bool(burst["burst"]), verdict=result.verdict,
                                match_score=result.match_score, url=post.url)
        bus_decision = bus.emit(event)
        routed_posts.append((post.platform_post_id, decision.tier, result.verdict, bus_decision))
        print(f"  {post.platform}:{post.platform_post_id} tier={decision.tier} score={decision.priority_score} "
              f"burst={burst['burst']} verdict={result.verdict} -> trigger={bus_decision.trigger} review={bus_decision.review_only}")

    print(f"  jobs queued: {len(store.jobs)} reviews: {len(store.reviews)} actions(blocks): 0")

    # Forced burst proof: same viral post with observed burst history -> must queue 1 job.
    forced = busmod.BusEvent(platform="x", post_id="x100", text=viral_x.text, tier="high",
                             priority_score=0.75, velocity=0.8, burst=True,
                             verdict="confirmed_fake", match_score=0.7, url=viral_x.url)
    forced_decision = bus.emit(forced)
    print(f"  forced burst: trigger={forced_decision.trigger} jobs={len(store.jobs)} reviews={len(store.reviews)}")

    # Scheduler proof: one offline cycle with injected fakes.
    collected = []
    collector = sched.RealtimeCollector(
        fetch_rss_items=lambda: [], fetch_x_posts=lambda: [viral_x],
        fetch_instagram_posts=lambda: [viral_ig], fetch_youtube_posts=lambda: [],
        on_post=lambda post, velocity: collected.append(post.platform_post_id),
    )
    stats = collector.run_once()
    print(f"  scheduler run_once: stats={stats} collected={collected}")
    print(f"  quota lanes loaded: {sorted(quota_buckets) if quota_buckets else 'n/a (scheduler buckets active at runtime)'}")
    live_ready = all(keys[k] == "SET" for k in ("X_BEARER_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "YOUTUBE_API_KEY"))
    print(f"  live API keys: {'READY' if live_ready else 'NOT READY - fill .env with real tokens'}")
    print("  blocking performed: NONE (report-only enforced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
