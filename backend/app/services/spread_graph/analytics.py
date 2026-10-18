"""Pure spread analytics (Stage2, no I/O) — burst + lightweight PageRank."""
from __future__ import annotations

import math
from typing import Dict, Iterable, List


def detect_burst(history: Iterable[float], threshold: float = 0.6) -> dict:
    """history: oldest->newest velocities 0-1. Burst if latest peak + sharp rise."""
    values = [max(0.0, min(1.0, float(v))) for v in history]
    if not values:
        return {"burst": False, "peak": 0.0, "rise": 0.0}
    peak = max(values)
    rise = values[-1] - values[0] if len(values) > 1 else values[-1]
    burst = peak >= threshold and rise >= 0.25
    return {"burst": burst, "peak": round(peak, 4), "rise": round(rise, 4)}


def pagerank(
    edges: Dict[str, List[str]],
    damping: float = 0.85,
    iters: int = 20,
) -> Dict[str, float]:
    """Minimal PageRank on account follow graph for offline ranking/tests."""
    nodes = set(edges) | {n for targets in edges.values() for n in targets}
    if not nodes:
        return {}
    rank = {n: 1.0 / len(nodes) for n in nodes}
    for _ in range(max(1, iters)):
        new_rank: Dict[str, float] = {}
        for node in nodes:
            inbound = sum(
                rank[src] / max(1, len(targets))
                for src, targets in edges.items()
                if node in targets
            )
            new_rank[node] = (1.0 - damping) / len(nodes) + damping * inbound
        total = sum(new_rank.values()) or 1.0
        rank = {k: v / total for k, v in new_rank.items()}
    return {k: round(float(v), 6) for k, v in rank.items()}


def spread_score(posts: int, engagement: int, followers: int) -> float:
    return round(posts * 2 + math.log1p(max(0, engagement)) + math.log1p(max(0, followers)) / 10.0, 4)
