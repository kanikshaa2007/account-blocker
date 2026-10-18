"""Monitor API (Stage6): reviewer queue, report-only actions."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

monitor_bp = Blueprint("monitor", __name__)

try:
    from ..services.eventbus.monitor_store import MonitorStore
except Exception:  # pragma: no cover - import-time fallback
    MonitorStore = None  # type: ignore


def _store():
    if MonitorStore is None:
        return None
    return MonitorStore.instance()


@monitor_bp.route("/queue", methods=["GET"])
def get_queue():
    store = _store()
    if store is None:
        return jsonify({"success": False, "error": "monitor unavailable"}), 500
    return jsonify({"success": True, "data": {"jobs": store.jobs, "reviews": store.reviews, "actions": store.actions, "sightings": store.sightings[-100:]}})


@monitor_bp.route("/approve", methods=["POST"])
def approve_job():
    store = _store()
    if store is None:
        return jsonify({"success": False, "error": "monitor unavailable"}), 500
    data = request.get_json() or {}
    job_id = data.get("job_id", "")
    reviewer = data.get("reviewer", "reviewer")
    if not job_id:
        return jsonify({"success": False, "error": "job_id required"}), 400
    try:
        job = store.approve(job_id, reviewer=reviewer)
    except KeyError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    # Report-only: we record a platform-report draft, never auto-block.
    return jsonify({"success": True, "data": job})


@monitor_bp.route("/ingest", methods=["POST"])
def ingest_live():
    """Run one live ingest cycle: free sources -> gate -> route -> verify -> queue.

    Uses only keyless public endpoints (Google News RSS India, PIB page,
    Reddit public JSON). Token-based X/Instagram/YouTube are skipped without keys.
    Report-only: queues jobs/reviews, never blocks.
    """
    store = _store()
    if store is None:
        return jsonify({"success": False, "error": "monitor unavailable"}), 500
    try:
        from ..services.connectors import live_sources
        from ..services.connectors import scoring as _scoring
        from ..services.moderation import router as _router
        from ..services.spread_graph import analytics as _analytics
        from ..services.verification import pib_client as _pib
        from ..services.verification import workers as _workers
        from ..services.verification import model_verifier as _model
        from ..services.eventbus import bus as _bus
        from ..services.eventbus import wiring as _wiring
    except Exception as exc:
        return jsonify({"success": False, "error": f"ingest deps unavailable: {exc}"}), 500

    data = request.get_json(silent=True) or {}
    queries = data.get("queries") or ["Government of India", "PIB fact check", "UPI", "Aadhaar"]
    limit = max(1, min(30, int(data.get("limit", 10))))
    summary: dict = {"fetched": {}, "routed": 0, "jobs": 0, "reviews": 0,
                     "skipped_offtopic": 0, "errors": []}

    # 1. Fetch free live sources.
    posts = []
    try:
        for query in queries:
            posts.extend(live_sources.fetch_google_news(query, limit=limit))
        summary["fetched"]["gnews"] = len(posts)
    except Exception as exc:
        summary["errors"].append(f"gnews: {exc}")
    try:
        facts_raw = live_sources.fetch_pib_factchecks(limit=20)
        summary["fetched"]["pib_facts"] = len(facts_raw)
    except Exception as exc:
        facts_raw = []
        summary["errors"].append(f"pib: {exc}")
    try:
        reddit_posts = live_sources.fetch_reddit_hot("india", limit=limit)
        posts.extend(reddit_posts)
        summary["fetched"]["reddit_json"] = len(reddit_posts)
    except Exception as exc:
        summary["errors"].append(f"reddit_json: {exc}")
    try:
        from ..config import Config as _Cfg
        rss_count, yt_count = 0, 0
        for sub in getattr(_Cfg, "REDDIT_SUBS", ["india"]):
            sub_posts = live_sources.fetch_reddit_rss(sub, limit=limit)
            posts.extend(sub_posts)
            rss_count += len(sub_posts)
        for entry in getattr(_Cfg, "YOUTUBE_CHANNELS", []):
            cid = entry if entry.startswith("UC") else live_sources.resolve_youtube_channel_id(entry)
            yt_posts = live_sources.fetch_youtube_channel_rss(cid, limit=limit)
            posts.extend(yt_posts)
            yt_count += len(yt_posts)
        summary["fetched"]["reddit_rss"] = rss_count
        summary["fetched"]["youtube_rss"] = yt_count
    except Exception as exc:
        summary["errors"].append(f"social_rss: {exc}")

    facts = [_pib.FactCheck(external_id=f"pib-{i}", title=f["title"], link=f["link"])
             for i, f in enumerate(facts_raw)]
    # Ground truth fallback: Google News items that ARE fact-check verdicts
    # (PIB homepage is ASP.NET without a public feed; these carry real verdicts).
    for j, post in enumerate(posts):
        lowered = (post.text or "").lower()
        if "fact check" in lowered and any(w in lowered for w in ("fake", "false", "misleading", "refutes", "debunk")):
            facts.append(_pib.FactCheck(external_id=f"gnews-fact-{j}", title=post.text[:300], link=post.url))
    summary["fetched"]["fact_pool"] = len(facts)

    # 2-5. Gate -> route -> burst -> verify -> bus.
    callbacks = _wiring.make_callbacks(store)
    bus = _bus.EventBus(start_simulation=callbacks["start_simulation"],
                        queue_report=callbacks["queue_report"])
    seen = set()
    for post in posts:
        key = f"{post.platform}:{post.platform_post_id}"
        if key in seen:
            continue
        seen.add(key)
        try:
            signal = _scoring.to_routing_input(post)
        except ValueError:
            summary["skipped_offtopic"] += 1
            continue
        decision = _scoring._router.route_post(signal)
        burst = _analytics.detect_burst([0.0, 0.0, float(signal.spread_velocity or 0.0)])
        result = _workers.verify_claim(post.text, facts, content_type=post.content_type,
                                       language=post.language,
                                       ml_fake_prob=_model.fake_probability(post.text))
        event = _bus.BusEvent(
            platform=post.platform, post_id=post.platform_post_id, text=post.text[:500],
            tier=decision.tier, priority_score=decision.priority_score,
            velocity=float(signal.spread_velocity or 0.0), burst=bool(burst["burst"]),
            verdict=result.verdict if result.verdict == "confirmed_fake" else "unverified",
            match_score=result.match_score, url=post.url)
        bus_decision = bus.emit(event)
        summary["routed"] += 1
        store.add_sighting({
            "platform": post.platform, "post_id": post.platform_post_id,
            "author": post.author_id, "text": post.text[:500], "url": post.url,
            "language": post.language,
            "content_type": post.content_type, "tier": decision.tier,
            "score": decision.priority_score, "verdict": event.verdict,
            "triggered": bus_decision.trigger, "ingested_at": post.created_at,
        })
        if bus_decision.trigger:
            summary["jobs"] += 1
        elif bus_decision.review_only:
            store.add_review(event)
            summary["reviews"] += 1

    summary["store"] = {"jobs": len(store.jobs), "reviews": len(store.reviews),
                        "actions": len(store.actions), "sightings": len(store.sightings)}
    return jsonify({"success": True, "data": summary})
