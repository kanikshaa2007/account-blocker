"""Shared normalized post shape for X / Instagram / YouTube (Stage1)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class NormalizedPost:
    platform: str  # x | instagram | youtube
    platform_post_id: str
    text: str = ""
    author_id: str = ""
    author_followers: int = 0
    language: Optional[str] = None  # e.g. en, hi
    content_type: str = "text"  # text | image | video | link | mixed
    # Raw engagement counters (all optional, missing => spread fallback)
    likes: int = 0
    shares: int = 0  # reposts / shares
    comments: int = 0
    views: int = 0
    created_at: str = ""
    url: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


def clamp01(value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number != number or number in (float("inf"), float("-inf")):
        return 0.0
    return max(0.0, min(1.0, number))
