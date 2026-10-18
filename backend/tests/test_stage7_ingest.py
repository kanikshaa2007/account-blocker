"""Stage7 ingest tests: live endpoint with stubbed fetchers (no network)."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from app import create_app
from app.services.eventbus.monitor_store import MonitorStore


def _post(platform="gnews", pid="p1", text="Government of India UPI update"):
    return SimpleNamespace(platform=platform, platform_post_id=pid, text=text,
                           author_id="src", author_followers=10, language="en",
                           content_type="link", likes=100, shares=50, comments=10,
                           views=5000, created_at="2026-10-16", url="https://x/y")


@pytest.fixture()
def app_client(monkeypatch):
    MonitorStore.reset()
    import app.api.monitor as monitor_api
    import app.services.connectors.live_sources as live

    monkeypatch.setattr(live, "fetch_google_news", lambda q, limit=10: [_post()])
    monkeypatch.setattr(live, "fetch_pib_factchecks",
                        lambda limit=20: [{"title": "PIB: viral UPI shutdown claim is fake",
                                           "link": "https://factcheck.pib.gov.in/1"}])
    monkeypatch.setattr(live, "fetch_reddit_hot", lambda sub="india", limit=10: [])
    monkeypatch.setattr(live, "fetch_reddit_rss", lambda sub="india", limit=10: [])
    monkeypatch.setattr(live, "fetch_youtube_channel_rss", lambda cid="", limit=10: [])

    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_ingest_runs_chain(app_client):
    resp = app_client.post("/api/monitor/ingest", json={"queries": ["UPI"], "limit": 5})
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    data = resp.get_json()["data"]
    assert data["fetched"]["gnews"] == 1
    assert data["routed"] == 1
    assert data["store"]["jobs"] + data["store"]["reviews"] >= 0

    queue = app_client.get("/api/monitor/queue").get_json()["data"]
    assert len(queue["jobs"]) + len(queue["reviews"]) == data["store"]["jobs"] + data["store"]["reviews"]
