"""Monitor store singleton (Stage6): reviewer queue, report-only."""
from __future__ import annotations

import time
from typing import Any, Dict, List


class MonitorStore:
    _instance = None

    def __init__(self) -> None:
        self.jobs: List[Dict[str, Any]] = []
        self.reviews: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.sightings: List[Dict[str, Any]] = []

    @classmethod
    def instance(cls) -> "MonitorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> "MonitorStore":
        cls._instance = cls()
        return cls._instance

    def add_job(self, event: Any, simulation: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
        job = {
            "job_id": f"job_{len(self.jobs) + 1}",
            "platform": getattr(event, "platform", "?"),
            "post_id": getattr(event, "post_id", "?"),
            "tier": getattr(event, "tier", "?"),
            "verdict": getattr(event, "verdict", "?"),
            "url": getattr(event, "url", ""),
            "text": getattr(event, "text", ""),
            "score": getattr(event, "priority_score", 0.0),
            "language": getattr(event, "language", "") if hasattr(event, "language") else "",
            "simulation": simulation, "report": report,
            "status": "queued", "created_at": time.time(),
        }
        self.jobs.append(job)
        return job

    def add_review(self, event: Any) -> Dict[str, Any]:
        item = {
            "review_id": f"rev_{len(self.reviews) + 1}",
            "platform": getattr(event, "platform", "?"),
            "post_id": getattr(event, "post_id", "?"),
            "tier": getattr(event, "tier", "?"),
            "verdict": getattr(event, "verdict", "?"),
            "status": "pending", "created_at": time.time(),
        }
        self.reviews.append(item)
        return item

    def approve(self, job_id: str, reviewer: str = "reviewer") -> Dict[str, Any]:
        for job in self.jobs:
            if job["job_id"] == job_id:
                job["status"] = "approved_report"
                action = {"job_id": job_id, "action": "report_platform", "reviewer": reviewer, "at": time.time()}
                self.actions.append(action)
                return job
        raise KeyError(f"job not found: {job_id}")

    def add_sighting(self, sighting: Dict[str, Any], cap: int = 100) -> Dict[str, Any]:
        """Every routed live post, even when it triggers nothing (visibility)."""
        self.sightings.append(sighting)
        del self.sightings[:-cap]
        return sighting
