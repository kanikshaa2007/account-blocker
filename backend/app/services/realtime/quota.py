"""Quota manager (Stage3, pure, no I/O): token-bucket + adaptive lanes.

Reduces X/IG/YT limits by polling fast only what is bursting.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TokenBucket:
    capacity: int
    refill_per_min: float
    _tokens: float = field(init=False)
    _last: float = field(init=False)

    def __post_init__(self) -> None:
        self._tokens = float(self.capacity)
        self._last = time.monotonic()

    def allow(self, cost: int = 1) -> bool:
        now = time.monotonic()
        elapsed_min = (now - self._last) / 60.0
        self._tokens = min(float(self.capacity), self._tokens + elapsed_min * self.refill_per_min)
        self._last = now
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False


@dataclass
class AdaptiveLanes:
    """fast lane for bursting claims, slow lane otherwise."""
    fast_interval_s: int = 120
    slow_interval_s: int = 600
    burst_velocity: float = 0.6

    def interval_for(self, velocity: float) -> int:
        return self.fast_interval_s if velocity >= self.burst_velocity else self.slow_interval_s


DEFAULT_BUDGETS: Dict[str, Dict[str, float]] = {
    # Conservative defaults; operator tunes to their plan quota.
    "x": {"capacity": 100, "refill_per_min": 5},
    "instagram": {"capacity": 100, "refill_per_min": 5},
    "youtube": {"capacity": 500, "refill_per_min": 20},
    "rss": {"capacity": 1000, "refill_per_min": 100},
}


def make_buckets(budgets: Dict[str, Dict[str, float]] | None = None) -> Dict[str, TokenBucket]:
    budgets = budgets or DEFAULT_BUDGETS
    return {
        name: TokenBucket(capacity=int(cfg["capacity"]), refill_per_min=float(cfg["refill_per_min"]))
        for name, cfg in budgets.items()
    }
