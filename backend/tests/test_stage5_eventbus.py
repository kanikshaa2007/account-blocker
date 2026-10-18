"""Stage5 event-bus tests (isolated: no app import, no I/O)."""
import importlib.util
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "eventbus"


def _load(name):
    mod_name = f"stage5_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _event(tier="urgent", burst=True, verdict="confirmed_fake"):
    bus = _load("bus")
    return bus, bus.BusEvent(
        platform="x", post_id="p1", text="Gov UPI shutdown claim",
        tier=tier, priority_score=0.9, velocity=0.8, burst=burst,
        verdict=verdict, match_score=0.7, url="https://x/i/p1",
    )


def test_trigger_fake_urgent_burst():
    bus_mod, event = _event()
    decision = bus_mod.should_trigger(event)
    assert decision.trigger is True and decision.review_only is False


def test_unverified_goes_to_review_only():
    bus_mod, event = _event(verdict="unverified")
    assert bus_mod.should_trigger(event).review_only is True
    collector = bus_mod.EventBus()
    decision = collector.emit(event)
    assert decision.review_only is True and len(collector.jobs) == 0 and len(collector.reviews) == 1


def test_no_trigger_low_or_no_burst():
    bus_mod, event = _event(tier="low", burst=False, verdict="confirmed_fake")
    assert bus_mod.should_trigger(event).trigger is False


def test_emit_queues_jobs_report_only():
    bus_mod, event = _event()
    calls = []
    bus = bus_mod.EventBus(
        start_simulation=lambda e: calls.append(("sim", e.post_id)) or {"simulation_id": "sim_1"},
        queue_report=lambda e: calls.append(("rep", e.post_id)) or {"report_id": "rep_1"},
    )
    decision = bus.emit(event)
    assert decision.trigger is True and len(bus.jobs) == 1
    assert calls == [("sim", "p1"), ("rep", "p1")]


def test_action_mode_guard():
    bus_mod, event = _event()
    bus = bus_mod.EventBus(action_mode="auto_block")
    try:
        bus.emit(event)
        assert False, "must reject non-report_only"
    except ValueError:
        pass
