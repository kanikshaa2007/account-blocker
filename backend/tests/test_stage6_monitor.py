"""Stage6 monitor tests: store + wiring + API (Flask test client)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from app import create_app
from app.services.eventbus.monitor_store import MonitorStore
from app.services.eventbus.wiring import make_callbacks
from app.services.eventbus.bus import BusEvent, EventBus


@pytest.fixture()
def app_client():
    MonitorStore.reset()
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def _fake_event():
    return BusEvent(platform="x", post_id="p9", text="Gov UPI shutdown claim",
                    tier="urgent", priority_score=0.9, velocity=0.8,
                    burst=True, verdict="confirmed_fake", url="https://x/i/p9")


def test_wiring_queues_job_and_api_approve(app_client):
    store = MonitorStore.instance()
    callbacks = make_callbacks(store)
    bus = EventBus(start_simulation=callbacks["start_simulation"],
                   queue_report=callbacks["queue_report"])
    decision = bus.emit(_fake_event())
    assert decision.trigger is True

    resp = app_client.get("/api/monitor/queue")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["jobs"]) == 1
    job_id = data["jobs"][0]["job_id"]

    resp2 = app_client.post("/api/monitor/approve", json={"job_id": job_id, "reviewer": "tester"})
    assert resp2.status_code == 200
    assert resp2.get_json()["data"]["status"] == "approved_report"

    resp3 = app_client.post("/api/monitor/approve", json={"job_id": "missing"})
    assert resp3.status_code == 404


def test_realtime_blueprint_registered(app_client):
    resp = app_client.get("/api/realtime/youtube/notify?hub.mode=subscribe&hub.challenge=abc")
    assert resp.status_code == 200
