"""EventBus (Stage5, pure + injectable, no I/O at import).

Trigger rule (conservative, report-only):
  tier in {high, urgent} AND burst AND verdict == confirmed_fake
  -> queue simulation + report job. Nothing blocks accounts.

Unverified urgent+burst -> review queue only, no auto-simulation.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class BusEvent:
    platform: str
    post_id: str
    text: str
    tier: str
    priority_score: float
    velocity: float
    burst: bool
    verdict: str
    match_score: float = 0.0
    url: str = ""


@dataclass(frozen=True)
class TriggerDecision:
    trigger: bool
    review_only: bool
    reason: str


def should_trigger(event: BusEvent) -> TriggerDecision:
    tier = (event.tier or "").lower()
    if tier in ("high", "urgent") and event.burst and event.verdict == "confirmed_fake":
        return TriggerDecision(True, False, f"tier={tier} burst verdict=fake -> simulate+report")
    if tier in ("high", "urgent") and event.burst and event.verdict == "unverified":
        return TriggerDecision(False, True, f"tier={tier} burst unverified -> human review, no auto-sim")
    return TriggerDecision(False, False, f"no trigger: tier={tier} burst={event.burst} verdict={event.verdict}")


@dataclass
class EventBus:
    start_simulation: Callable[[BusEvent], Dict[str, Any]] | None = None
    queue_report: Callable[[BusEvent], Dict[str, Any]] | None = None
    action_mode: str = field(default_factory=lambda: os.environ.get("ACTION_MODE", "report_only"))

    def __post_init__(self) -> None:
        self.jobs: List[Dict[str, Any]] = []
        self.reviews: List[BusEvent] = []

    def emit(self, event: BusEvent) -> TriggerDecision:
        if self.action_mode != "report_only":
            raise ValueError(f"Stage5 only allows report_only, got {self.action_mode}")
        decision = should_trigger(event)
        if decision.trigger:
            sim = self.start_simulation(event) if self.start_simulation else {"simulation_id": f"sim_{event.platform}_{event.post_id}", "status": "queued"}
            rep = self.queue_report(event) if self.queue_report else {"report_id": f"rep_{event.platform}_{event.post_id}", "status": "queued"}
            self.jobs.append({"event": event, "simulation": sim, "report": rep})
        elif decision.review_only:
            self.reviews.append(event)
        return decision
