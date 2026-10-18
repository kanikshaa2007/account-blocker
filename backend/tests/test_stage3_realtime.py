"""Stage3 realtime tests (isolated: no network, no Neo4j, no Flask required)."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "realtime"


def _load(name):
    mod_name = f"stage3_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _post(platform="x", pid="1"):
    return SimpleNamespace(platform=platform, platform_post_id=pid)


def test_quota_bucket_and_lanes():
    quota = _load("quota")
    bucket = quota.TokenBucket(capacity=2, refill_per_min=0)
    assert bucket.allow() is True
    assert bucket.allow() is True
    assert bucket.allow() is False  # exhausted, no refill
    lanes = quota.AdaptiveLanes(fast_interval_s=120, slow_interval_s=600, burst_velocity=0.6)
    assert lanes.interval_for(0.9) == 120
    assert lanes.interval_for(0.1) == 600


def test_rss_parse_and_webhook_verify():
    webhooks = _load("webhooks")
    xml = """<rss><channel>
      <item><title>PIB fact check on UPI</title><link>https://x/y</link><guid>g1</guid><pubDate>d</pubDate></item>
      <item><title></title><link></link></item>
      </channel></rss>"""
    items = webhooks.parse_rss(xml, source="pib")
    assert len(items) == 1 and items[0].title.startswith("PIB")
    assert webhooks.parse_rss("not xml") == []
    ok, challenge = webhooks.verify_instagram_webhook(
        {"hub.mode": "subscribe", "hub.verify_token": "tok", "hub.challenge": "ch"},
        verify_token="tok",
    )
    assert (ok, challenge) == (True, "ch")
    assert webhooks.verify_instagram_webhook({"hub.mode": "subscribe"}, verify_token="tok") == (False, "")
    ok, ch = webhooks.verify_pubsubhubbub({"hub.mode": "subscribe", "hub.challenge": "abc"})
    assert (ok, ch) == (True, "abc")
    ids = webhooks.parse_instagram_webhook_payload({"entry": [{"changes": [{"value": {"media_id": "m1"}}]}]})
    assert ids == ["m1"]


def test_scheduler_dedup_and_stats():
    scheduler = _load("scheduler")
    seen_posts = []
    collector = scheduler.RealtimeCollector(
        fetch_rss_items=lambda: [_post("rss", "r1"), _post("rss", "r1")],
        fetch_x_posts=lambda: [_post("x", "x1")],
        fetch_instagram_posts=lambda: [],
        fetch_youtube_posts=lambda: [],
        on_post=lambda post, velocity: seen_posts.append(post),
    )
    stats = collector.run_once()
    assert stats["rss"] == 1  # duplicate within cycle deduped
    assert stats["routed"] == 2
    stats2 = collector.run_once()
    assert stats2["routed"] == 2  # second cycle all deduped, no growth
    assert len(seen_posts) == 2
