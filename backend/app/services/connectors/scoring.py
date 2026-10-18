"""NormalizedPost -> RoutingInput scoring (Stage1, pure functions).

Spread is triage speed only, never evidence of falsity.
Missing metrics => spread_reliable=False so the router uses its fallback.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

try:
    from .gov_topics import mentions_gov
    from .models import NormalizedPost, clamp01
except ImportError:  # isolated file-path loading in tests
    _base = Path(__file__).resolve().parent

    def _load(_name: str):
        import sys as _sys
        _mod_name = f"{__name__}.{_name}" if __name__ else _name
        _spec = importlib.util.spec_from_file_location(_mod_name, _base / f"{_name}.py")
        _mod = importlib.util.module_from_spec(_spec)
        _sys.modules[_mod_name] = _mod
        _spec.loader.exec_module(_mod)
        return _mod

    _gov = _load("gov_topics")
    _models = _load("models")
    mentions_gov = _gov.mentions_gov
    NormalizedPost = _models.NormalizedPost
    clamp01 = _models.clamp01

_ROUTER_PATH = Path(__file__).resolve().parents[1] / "moderation" / "router.py"
_spec = importlib.util.spec_from_file_location("stage1_router", _ROUTER_PATH)
_router = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_router)
RoutingInput = _router.RoutingInput  # re-export for collectors/tests


def _log10_scaled(value: float, pivot: float = 1000.0) -> float:
    if value <= 0:
        return 0.0
    return clamp01(math.log10(1.0 + value) / math.log10(1.0 + pivot))


def spread_velocity(post: NormalizedPost, cross_platform_match: float = 0.0) -> tuple[float, bool]:
    """Return (velocity_0_1, reliable). Unreliable when no engagement signal."""
    total_signals = post.likes + post.shares + post.comments + post.views
    if total_signals <= 0:
        return 0.0, False
    # Reshare rate: shares+comments vs views (or vs likes when views missing)
    denom = post.views if post.views > 0 else (post.likes + post.shares + post.comments + 1)
    reshare_rate = clamp01((post.shares + post.comments) / max(1, denom) * 4.0)
    follower_amp = _log10_scaled(post.shares * 10 + post.likes, pivot=5000.0)
    cross = clamp01(cross_platform_match)
    velocity = clamp01(0.5 * reshare_rate + 0.3 * follower_amp + 0.2 * cross)
    return velocity, True


def to_routing_input(
    post: NormalizedPost,
    cross_platform_match: float = 0.0,
    evidence_uncertainty: float = 0.7,
    verification_complexity: float = 0.0,
) -> RoutingInput:
    """Map one collected post to router input. Raises ValueError if off-topic."""
    if not mentions_gov(post.text):
        raise ValueError("post does not mention a gov-of-India topic, skipped")
    velocity, reliable = spread_velocity(post, cross_platform_match)
    # Harm: gov-topic base 0.7; +0.15 for video/mixed (harder to debunk quickly)
    harm = 0.7 + (0.15 if post.content_type in ("video", "mixed") else 0.0)
    # Complexity: video/audio/link need forensics/transcription
    complexity = verification_complexity or (0.6 if post.content_type in ("video", "audio", "mixed") else 0.3)
    return RoutingInput(
        harm_if_false=clamp01(harm),
        evidence_uncertainty=clamp01(evidence_uncertainty),
        verification_complexity=clamp01(complexity),
        spread_velocity=velocity if reliable else None,
        spread_reliable=reliable,
        language=post.language,
        content_type=post.content_type,
        platform=post.platform,
        platform_post_id=post.platform_post_id,
    )
