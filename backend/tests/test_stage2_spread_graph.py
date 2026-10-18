"""Stage2 spread-graph tests (isolated: fake driver, no Neo4j server)."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "spread_graph"


def _load(name):
    mod_name = f"stage2_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeResult(list):
    pass


class _FakeSession:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, query, params=None):
        self.driver.ran.append((query.strip()[:60], params))
        if "spread_score" in query:
            return _FakeResult([{"platform": "x", "account_id": "a1", "spread_score": 9.5}])
        if "peak" in query:
            return _FakeResult([{"platform": "x", "post_id": "p1", "peak": 0.9}])
        return _FakeResult([])


class _FakeDriver:
    def __init__(self):
        self.ran = []

    def session(self):
        return _FakeSession(self)


def test_analytics_burst_and_pagerank():
    analytics = _load("analytics")
    assert analytics.detect_burst([0.1, 0.2, 0.9])["burst"] is True
    assert analytics.detect_burst([0.1, 0.12])["burst"] is False
    ranks = analytics.pagerank({"a": ["b"], "b": ["c"], "c": ["a", "b"]})
    assert abs(sum(ranks.values()) - 1.0) < 1e-6
    assert analytics.spread_score(3, 100, 50) > analytics.spread_score(1, 10, 5)


def test_store_disabled_without_creds():
    store_mod = _load("store")
    store = store_mod.Neo4jStore(driver=None, password="")
    import os
    if os.environ.get("NEO4J_PASSWORD"):
        return  # live env: skip disabled assertion
    assert store.enabled is False
    assert store.superspreaders() == []
    post = SimpleNamespace(platform="x", platform_post_id="p1", text="t",
                           author_id="a", author_followers=1, content_type="text",
                           language="en", likes=1, shares=1, comments=0, views=10,
                           created_at="", url="")
    store.upsert_post(post, claim_key="k")  # no-op, must not raise


def test_store_fake_driver_flow():
    store_mod = _load("store")
    fake = _FakeDriver()
    store = store_mod.Neo4jStore(driver=fake)
    assert store.enabled is True
    store.ensure_schema()
    post = SimpleNamespace(platform="instagram", platform_post_id="ig1", text="PM-KISAN update",
                           author_id="acc1", author_followers=100, content_type="video",
                           language="hi", likes=50, shares=20, comments=5, views=1000,
                           created_at="2026-01-01", url="http://x")
    store.upsert_post(post, claim_key="pm-kisan", topic="PM-KISAN")
    store.record_velocity("instagram", "ig1", 0.75, post)
    store.add_follow("instagram", "acc1", "acc2")
    assert store.superspreaders(limit=5)[0]["account_id"] == "a1"
    assert store.burst_posts("2026-01-01T00:00:00+00:00")[0]["post_id"] == "p1"
    payload = store.to_zep_payload(post, 0.75, tier="high")
    assert payload["metadata"]["velocity"] == 0.75
    assert len(fake.ran) >= 6
