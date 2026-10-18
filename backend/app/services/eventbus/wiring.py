"""Runner wiring (Stage6): EventBus callbacks -> MonitorStore + SimulationManager.

Production wiring does NOT auto-run heavy OASIS; it queues a simulation
request linked to the monitor job. Operator starts it from the dashboard
or an existing project. Report-only is enforced upstream in EventBus.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

try:
    from .monitor_store import MonitorStore
except ImportError:
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _Path
    _base = _Path(__file__).resolve().parent

    def _load(_name: str):
        _mod_name = f"{__name__}.{_name}" if __name__ else _name
        _spec = _ilu.spec_from_file_location(_mod_name, _base / f"{_name}.py")
        _mod = _ilu.module_from_spec(_spec)
        _sys.modules[_mod_name] = _mod
        _spec.loader.exec_module(_mod)
        return _mod

    MonitorStore = _load("monitor_store").MonitorStore


def make_callbacks(store: MonitorStore | None = None) -> Dict[str, Callable[[Any], Dict[str, Any]]]:
    store = store or MonitorStore.instance()

    def start_simulation(event: Any) -> Dict[str, Any]:
        simulation = {
            "simulation_id": f"sim_{event.platform}_{event.post_id}",
            "status": "queued",
            "requirement": f"Forecast spread of {event.platform}:{event.post_id} ({event.text[:140]})",
        }
        return simulation

    def queue_report(event: Any) -> Dict[str, Any]:
        report = {"report_id": f"rep_{event.platform}_{event.post_id}", "status": "queued"}
        store.add_job(event, start_simulation(event), report)
        return report

    def queue_review(event: Any) -> Dict[str, Any]:
        return store.add_review(event)

    return {"start_simulation": start_simulation, "queue_report": queue_report, "queue_review": queue_review}
