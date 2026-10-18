"""Deterministic moderation-priority routing (Stage 1).

The score represents **verification urgency, not the probability that
content is false**. Popularity/virality alone never implies guilt and
protected characteristics are never used as signals.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

LOW = "low"
NORMAL = "normal"
HIGH = "high"
URGENT = "urgent"


class PriorityTier:
    """Allowed priority tier labels."""

    LOW = LOW
    NORMAL = NORMAL
    HIGH = HIGH
    URGENT = URGENT
    ALL = (LOW, NORMAL, HIGH, URGENT)


SUPPORTED_CONTENT_TYPES = ("text", "image", "video", "audio", "link", "mixed")
SUPPORTED_WORKERS = (
    "text_verifier",
    "image_forensics",
    "video_forensics",
    "audio_transcriber",
    "source_credibility",
    "multilingual_retriever",
    "evidence_synthesizer",
)


def _validate_normalized(name: str, value: float) -> float:
    """Validate a 0.0-1.0 signal and reject NaN/inf/negative/out-of-range."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number in [0.0, 1.0], got {value!r}")
    numeric = float(value)
    if math.isnan(numeric):
        raise ValueError(f"{name} must not be NaN")
    if math.isinf(numeric):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if numeric < 0.0 or numeric > 1.0:
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value!r}")
    return numeric


@dataclass(frozen=True)
class RoutingWeights:
    """Relative contribution of each signal. Normalised by total at scoring."""

    harm: float = 0.45
    uncertainty: float = 0.25
    spread: float = 0.20
    complexity: float = 0.10

    def __post_init__(self) -> None:
        for name in ("harm", "uncertainty", "spread", "complexity"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"weight {name} must be a number, got {value!r}")
            numeric = float(value)
            if math.isnan(numeric) or math.isinf(numeric):
                raise ValueError(f"weight {name} must be finite, got {value!r}")
            if numeric < 0.0:
                raise ValueError(f"weight {name} must be >= 0, got {value!r}")
        if float(self.harm + self.uncertainty + self.spread + self.complexity) <= 0.0:
            raise ValueError("at least one routing weight must be > 0")


@dataclass(frozen=True)
class RoutingThresholds:
    """Tier cutoffs applied to the normalised 0.0-1.0 score."""

    low_max: float = 0.35
    high_min: float = 0.60
    urgent_min: float = 0.80

    def __post_init__(self) -> None:
        low = _validate_normalized("low_max", self.low_max)
        high = _validate_normalized("high_min", self.high_min)
        urgent = _validate_normalized("urgent_min", self.urgent_min)
        if not (low < high < urgent):
            raise ValueError(
                f"thresholds must satisfy low_max < high_min < urgent_min, got "
                f"{low}, {high}, {urgent}"
            )


@dataclass(frozen=True)
class RoutingConfig:
    """Configurable routing behaviour."""

    weights: RoutingWeights = field(default_factory=RoutingWeights)
    thresholds: RoutingThresholds = field(default_factory=RoutingThresholds)
    default_spread_when_missing: float = 0.30
    max_workers: int = 3

    def __post_init__(self) -> None:
        _validate_normalized(
            "default_spread_when_missing", self.default_spread_when_missing
        )
        if not isinstance(self.max_workers, int) or isinstance(self.max_workers, bool):
            raise ValueError(f"max_workers must be an int, got {self.max_workers!r}")
        if self.max_workers < 1 or self.max_workers > 5:
            raise ValueError(
                f"max_workers must be in [1, 5], got {self.max_workers!r}"
            )


@dataclass(frozen=True)
class RoutingInput:
    """Validated, platform-neutral moderation signal.

    Platform connectors normalise their native fields into this shape.
    `platform` / `platform_post_id` are opaque passthrough metadata and
    never affect the score.
    """

    harm_if_false: float
    evidence_uncertainty: float
    verification_complexity: float
    spread_velocity: Optional[float] = None
    spread_reliable: bool = True
    language: Optional[str] = None
    content_type: Optional[str] = None
    platform: Optional[str] = None
    platform_post_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "harm_if_false", _validate_normalized(
                "harm_if_false", self.harm_if_false
            )
        )
        object.__setattr__(
            self, "evidence_uncertainty", _validate_normalized(
                "evidence_uncertainty", self.evidence_uncertainty
            )
        )
        object.__setattr__(
            self, "verification_complexity", _validate_normalized(
                "verification_complexity", self.verification_complexity
            )
        )
        if self.spread_velocity is not None:
            object.__setattr__(
                self, "spread_velocity", _validate_normalized(
                    "spread_velocity", self.spread_velocity
                )
            )
        if not isinstance(self.spread_reliable, bool):
            raise ValueError(
                f"spread_reliable must be a bool, got {self.spread_reliable!r}"
            )
        for name in ("language", "content_type", "platform", "platform_post_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string or None")


@dataclass(frozen=True)
class RoutingDecision:
    """Structured routing result (urgency only, never a truth verdict)."""

    priority_score: float
    tier: str
    reasons: List[str]
    selected_workers: List[str]
    worker_budget: int
    explanation: str
    deferred_workers: List[str] = field(default_factory=list)
    spread_is_estimate: bool = False
    spread_effective: float = 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "priority_score": self.priority_score,
            "tier": self.tier,
            "reasons": list(self.reasons),
            "selected_workers": list(self.selected_workers),
            "worker_budget": self.worker_budget,
            "explanation": self.explanation,
            "deferred_workers": list(self.deferred_workers),
            "spread_is_estimate": self.spread_is_estimate,
            "spread_effective": self.spread_effective,
        }


def _tier_for_score(score: float, thresholds: RoutingThresholds) -> str:
    if score >= thresholds.urgent_min:
        return URGENT
    if score >= thresholds.high_min:
        return HIGH
    if score > thresholds.low_max:
        return NORMAL
    return LOW


def _candidate_workers(
    content_type: Optional[str],
    language: Optional[str],
    uncertainty: float,
    complexity: float,
) -> List[str]:
    """Deterministic capability-aware candidate list (before budget cut).

    Order encodes capability priority, most essential first:
    - modality specialist (image/video/audio forensics, transcriber) comes
      before generic text claim extraction for non-text inputs, because the
      modality capability cannot be replaced by text analysis alone;
    - text_verifier is always present (claim extraction base);
    - source_credibility follows when evidence is uncertain;
    - multilingual_retriever follows when language is non-English;
    - evidence_synthesizer is last (aggregation step).
    Truncation by budget therefore drops from the least essential end
    first, and anything dropped is reported in `deferred_workers`,
    never silently.
    """
    normalized_content = (content_type or "").strip().lower()
    if normalized_content == "image":
        candidates = ["image_forensics", "text_verifier"]
    elif normalized_content == "video":
        candidates = ["video_forensics", "text_verifier"]
    elif normalized_content == "audio":
        candidates = ["audio_transcriber", "text_verifier"]
    elif normalized_content == "link":
        candidates = ["text_verifier", "source_credibility"]
    elif normalized_content == "mixed":
        candidates = ["text_verifier", "image_forensics", "video_forensics"]
    else:
        # Default covers text, unknown, and missing content types.
        candidates = ["text_verifier"]

    if uncertainty >= 0.5 and "source_credibility" not in candidates:
        candidates.append("source_credibility")
    normalized_language = (language or "").strip().lower()
    if normalized_language and normalized_language != "en":
        if "multilingual_retriever" not in candidates:
            candidates.append("multilingual_retriever")
    if (uncertainty >= 0.6 or complexity >= 0.6) and (
        "evidence_synthesizer" not in candidates
    ):
        candidates.append("evidence_synthesizer")

    return candidates


def _select_workers(
    content_type: Optional[str],
    language: Optional[str],
    uncertainty: float,
    complexity: float,
    max_workers: int,
) -> List[str]:
    """Deterministically select compatible verification workers.

    Kept for backward compatibility; prefer `route_post` which also
    reports `deferred_workers`.
    """
    return _candidate_workers(
        content_type, language, uncertainty, complexity
    )[:max_workers]


def _worker_budget(
    uncertainty: float,
    complexity: float,
    max_workers: int,
    language: Optional[str] = None,
    content_type: Optional[str] = None,
) -> int:
    """Bounded budget: multimodal/complex/uncertain/non-English get head start."""
    budget = 1
    normalized_content = (content_type or "").strip().lower()
    if normalized_content in ("image", "video", "audio", "mixed", "link"):
        # These modalities need at least 2 capabilities (specialist + text).
        budget += 1
    if complexity >= 0.5:
        budget += 1
    if uncertainty >= 0.6:
        budget += 1
    normalized_language = (language or "").strip().lower()
    if normalized_language and normalized_language != "en":
        budget += 1
    return max(1, min(max_workers, budget))


def route_post(
    signal: RoutingInput,
    config: Optional[RoutingConfig] = None,
) -> RoutingDecision:
    """Route one post to verification workers.

    Pure function: no I/O, no randomness, identical inputs always give
    identical outputs.
    """
    if not isinstance(signal, RoutingInput):
        raise ValueError("signal must be a RoutingInput")
    cfg = config or RoutingConfig()

    spread_missing = signal.spread_velocity is None or not signal.spread_reliable
    spread_effective = (
        cfg.default_spread_when_missing if spread_missing else signal.spread_velocity
    )
    assert spread_effective is not None  # validated above / config default

    total = (
        cfg.weights.harm
        + cfg.weights.uncertainty
        + cfg.weights.spread
        + cfg.weights.complexity
    )
    raw = (
        cfg.weights.harm * signal.harm_if_false
        + cfg.weights.uncertainty * signal.evidence_uncertainty
        + cfg.weights.spread * float(spread_effective)
        + cfg.weights.complexity * signal.verification_complexity
    ) / total
    score = round(max(0.0, min(1.0, raw)), 4)
    tier = _tier_for_score(score, cfg.thresholds)

    reasons: List[str] = [
        f"Potential harm if false: {signal.harm_if_false:.2f}.",
        f"Evidence uncertainty: {signal.evidence_uncertainty:.2f} "
        "(higher means less or more conflicting evidence).",
    ]
    if spread_missing:
        reasons.append(
            "Spread unavailable: fallback estimate "
            f"{cfg.default_spread_when_missing:.2f} used. "
            "This is a neutral triage estimate, NOT an observed measurement, "
            "and must not be read as evidence of falsity or guilt."
        )
    else:
        reasons.append(
            f"Observed spread velocity: {float(signal.spread_velocity):.2f} "
            "(used only for triage speed, not as evidence of falsity)."
        )
    reasons.append(
        f"Verification complexity: {signal.verification_complexity:.2f}."
    )
    if signal.language:
        reasons.append(f"Language metadata: {signal.language} (worker matching only).")
    if signal.content_type:
        reasons.append(
            f"Content type: {signal.content_type} (worker matching only)."
        )

    budget = _worker_budget(
        signal.evidence_uncertainty,
        signal.verification_complexity,
        cfg.max_workers,
        signal.language,
        signal.content_type,
    )
    candidates = _candidate_workers(
        signal.content_type,
        signal.language,
        signal.evidence_uncertainty,
        signal.verification_complexity,
    )
    workers = candidates[:budget]
    deferred = candidates[budget:]
    if deferred:
        reasons.append(
            f"Worker budget {budget} deferred {len(deferred)} capability(ies): "
            f"{', '.join(deferred)}. Re-run with a higher budget to include them; "
            "nothing was silently dropped."
        )

    explanation = (
        f"Score {score:.4f} -> tier '{tier}'. This is verification urgency, "
        "not a truth/falsity verdict. "
        f"Selected {len(workers)} worker(s) within budget {budget}: "
        f"{', '.join(workers)}."
    )
    if deferred:
        explanation += (
            f" Deferred due to budget: {', '.join(deferred)}."
        )
    if spread_missing:
        explanation += " Spread value is a fallback estimate, not observed."
    return RoutingDecision(
        priority_score=score,
        tier=tier,
        reasons=reasons,
        selected_workers=workers,
        worker_budget=budget,
        explanation=explanation,
        deferred_workers=deferred,
        spread_is_estimate=spread_missing,
        spread_effective=float(spread_effective),
    )
