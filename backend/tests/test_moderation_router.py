"""Stage 1 router tests (isolated: no app package import, no third-party deps)."""

import importlib.util
import math
from pathlib import Path

import pytest

_ROUTER_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "services"
    / "moderation"
    / "router.py"
)
_spec = importlib.util.spec_from_file_location(
    "moderation_router_isolated", _ROUTER_PATH
)
_router = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_router)

RoutingConfig = _router.RoutingConfig
RoutingInput = _router.RoutingInput
RoutingThresholds = _router.RoutingThresholds
RoutingWeights = _router.RoutingWeights
route_post = _router.route_post


def _low_signal(**overrides):
    base = {
        "harm_if_false": 0.1,
        "evidence_uncertainty": 0.2,
        "verification_complexity": 0.2,
        "spread_velocity": 0.1,
        "spread_reliable": True,
        "language": "en",
        "content_type": "text",
    }
    base.update(overrides)
    return RoutingInput(**base)


def _urgent_signal(**overrides):
    base = {
        "harm_if_false": 0.95,
        "evidence_uncertainty": 0.85,
        "verification_complexity": 0.7,
        "spread_velocity": 0.8,
        "spread_reliable": True,
        "language": "hi",
        "content_type": "video",
    }
    base.update(overrides)
    return RoutingInput(**base)


def test_low_priority_example():
    decision = route_post(_low_signal())
    assert decision.tier == "low"
    assert 0.0 <= decision.priority_score <= 0.35
    assert decision.worker_budget >= 1


def test_urgent_verification_example():
    decision = route_post(_urgent_signal())
    assert decision.tier == "urgent"
    assert decision.priority_score >= 0.80
    assert "urgency" in decision.explanation.lower()
    assert "not a truth" in decision.explanation.lower()


def test_conflicting_evidence_increases_urgency():
    low_uncertainty = route_post(_low_signal(evidence_uncertainty=0.1))
    high_uncertainty = route_post(_low_signal(evidence_uncertainty=0.9))
    assert high_uncertainty.priority_score > low_uncertainty.priority_score


def test_missing_spread_uses_neutral_baseline():
    missing = route_post(_low_signal(spread_velocity=None))
    config = RoutingConfig()
    assert missing.priority_score == pytest.approx(
        round(
            (
                0.45 * 0.1
                + 0.25 * 0.2
                + 0.20 * config.default_spread_when_missing
                + 0.10 * 0.2
            ),
            4,
        )
    )
    assert missing.spread_is_estimate is True
    assert missing.spread_effective == pytest.approx(
        config.default_spread_when_missing
    )
    assert any("fallback estimate" in r.lower() for r in missing.reasons)
    assert any("not an observed measurement" in r.lower() for r in missing.reasons)


def test_unreliable_spread_flag_uses_baseline():
    unreliable = route_post(
        _low_signal(spread_velocity=1.0, spread_reliable=False)
    )
    missing = route_post(_low_signal(spread_velocity=None))
    assert unreliable.priority_score == missing.priority_score
    assert unreliable.spread_is_estimate is True
    assert any("fallback estimate" in r.lower() for r in unreliable.reasons)


def test_observed_spread_never_labeled_estimate():
    decision = route_post(_low_signal(spread_velocity=0.7, spread_reliable=True))
    assert decision.spread_is_estimate is False
    assert decision.spread_effective == pytest.approx(0.7)
    assert any("observed spread velocity" in r.lower() for r in decision.reasons)
    assert not any("fallback estimate" in r.lower() for r in decision.reasons)


def test_virality_alone_does_not_imply_urgent():
    # Maximum spread but minimal harm/uncertainty/complexity stays low.
    decision = route_post(
        _low_signal(
            harm_if_false=0.1,
            evidence_uncertainty=0.1,
            verification_complexity=0.1,
            spread_velocity=1.0,
            spread_reliable=True,
        )
    )
    assert decision.tier == "low"


@pytest.mark.parametrize(
    "field,value",
    [
        ("harm_if_false", float("nan")),
        ("harm_if_false", float("inf")),
        ("harm_if_false", -0.1),
        ("harm_if_false", 1.5),
        ("evidence_uncertainty", float("nan")),
        ("evidence_uncertainty", float("-inf")),
        ("evidence_uncertainty", -1.0),
        ("evidence_uncertainty", 2.0),
        ("verification_complexity", float("nan")),
        ("verification_complexity", float("inf")),
        ("verification_complexity", -0.01),
        ("verification_complexity", 1.01),
        ("spread_velocity", float("nan")),
        ("spread_velocity", float("inf")),
        ("spread_velocity", -0.5),
        ("spread_velocity", 5.0),
    ],
)
def test_invalid_values_rejected(field, value):
    kwargs = {
        "harm_if_false": 0.5,
        "evidence_uncertainty": 0.5,
        "verification_complexity": 0.5,
    }
    kwargs[field] = value
    with pytest.raises(ValueError):
        RoutingInput(**kwargs)


def test_boundary_values_accepted():
    decision = route_post(
        RoutingInput(
            harm_if_false=0.0,
            evidence_uncertainty=0.0,
            verification_complexity=0.0,
            spread_velocity=0.0,
        )
    )
    assert decision.priority_score == 0.0
    assert decision.tier == "low"

    decision = route_post(
        RoutingInput(
            harm_if_false=1.0,
            evidence_uncertainty=1.0,
            verification_complexity=1.0,
            spread_velocity=1.0,
        )
    )
    assert decision.priority_score == 1.0
    assert decision.tier == "urgent"


def test_bool_is_rejected_as_numeric():
    with pytest.raises(ValueError):
        RoutingInput(
            harm_if_false=True,  # type: ignore[arg-type]
            evidence_uncertainty=0.5,
            verification_complexity=0.5,
        )


def test_determinism_repeated_inputs():
    signal = _urgent_signal()
    first = route_post(signal)
    second = route_post(signal)
    assert first.to_dict() == second.to_dict()


def test_default_config_values():
    config = RoutingConfig()
    assert (config.weights.harm, config.weights.uncertainty) == (0.45, 0.25)
    assert (config.weights.spread, config.weights.complexity) == (0.20, 0.10)
    assert (
        config.thresholds.low_max,
        config.thresholds.high_min,
        config.thresholds.urgent_min,
    ) == (0.35, 0.60, 0.80)
    assert config.default_spread_when_missing == pytest.approx(0.30)
    assert config.max_workers == 3


def test_configurable_thresholds_change_tier():
    signal = _low_signal(
        harm_if_false=0.5, evidence_uncertainty=0.5, verification_complexity=0.5,
        spread_velocity=0.5,
    )
    default_tier = route_post(signal).tier
    strict = RoutingConfig(
        thresholds=RoutingThresholds(low_max=0.1, high_min=0.2, urgent_min=0.3)
    )
    assert route_post(signal, strict).tier != default_tier or default_tier in (
        "high",
        "urgent",
    )
    assert route_post(signal, strict).tier in ("normal", "high", "urgent")


def test_configurable_weights_change_score():
    signal = _urgent_signal()
    harm_heavy = RoutingConfig(
        weights=RoutingWeights(harm=0.9, uncertainty=0.05, spread=0.03, complexity=0.02)
    )
    spread_heavy = RoutingConfig(
        weights=RoutingWeights(harm=0.02, uncertainty=0.03, spread=0.9, complexity=0.05)
    )
    assert (
        route_post(signal, harm_heavy).priority_score
        != route_post(signal, spread_heavy).priority_score
    )


def test_invalid_weights_and_thresholds_rejected():
    with pytest.raises(ValueError):
        RoutingWeights(harm=-0.1)
    with pytest.raises(ValueError):
        RoutingWeights(harm=0.0, uncertainty=0.0, spread=0.0, complexity=0.0)
    with pytest.raises(ValueError):
        RoutingThresholds(low_max=0.9, high_min=0.5, urgent_min=0.8)
    with pytest.raises(ValueError):
        RoutingConfig(max_workers=0)
    with pytest.raises(ValueError):
        RoutingConfig(max_workers=99)


def test_worker_selection_by_content_type():
    image = route_post(_low_signal(content_type="image"))
    assert "image_forensics" in image.selected_workers
    video = route_post(_low_signal(content_type="video"))
    assert "video_forensics" in video.selected_workers
    audio = route_post(_low_signal(content_type="audio"))
    assert "audio_transcriber" in audio.selected_workers


def test_multilingual_worker_selected_for_non_english():
    english = route_post(_low_signal(language="en"))
    hindi = route_post(_low_signal(language="hi"))
    assert "multilingual_retriever" not in english.selected_workers
    assert "multilingual_retriever" in hindi.selected_workers


def test_small_budget_reports_deferred_multilingual_text():
    config = RoutingConfig(max_workers=1)
    decision = route_post(_low_signal(language="hi", content_type="text"), config)
    assert decision.worker_budget == 1
    assert len(decision.selected_workers) == 1
    # Full need is text_verifier + multilingual_retriever; one must defer.
    assert decision.deferred_workers == ["multilingual_retriever"]
    assert any("deferred" in r.lower() for r in decision.reasons)
    assert "deferred" in decision.explanation.lower()


def test_small_budget_reports_deferred_image():
    config = RoutingConfig(max_workers=1)
    decision = route_post(_low_signal(language="en", content_type="image"), config)
    assert decision.selected_workers == ["image_forensics"]
    assert decision.deferred_workers == ["text_verifier"]
    assert any("text_verifier" in r for r in decision.reasons)


def test_small_budget_reports_deferred_video():
    config = RoutingConfig(max_workers=1)
    decision = route_post(_low_signal(language="en", content_type="video"), config)
    assert decision.selected_workers == ["video_forensics"]
    assert decision.deferred_workers == ["text_verifier"]


def test_small_budget_reports_deferred_audio():
    config = RoutingConfig(max_workers=1)
    decision = route_post(_low_signal(language="en", content_type="audio"), config)
    assert decision.selected_workers == ["audio_transcriber"]
    assert decision.deferred_workers == ["text_verifier"]


def test_multimodal_default_budget_covers_both_capabilities():
    decision = route_post(_low_signal(language="en", content_type="image"))
    assert "image_forensics" in decision.selected_workers
    assert "text_verifier" in decision.selected_workers
    assert decision.deferred_workers == []


def test_worker_budget_is_bounded():
    config = RoutingConfig(max_workers=2)
    decision = route_post(_urgent_signal(), config)
    assert decision.worker_budget <= 2
    assert len(decision.selected_workers) <= 2
    assert len(decision.selected_workers) <= decision.worker_budget
    # Nothing silently dropped: selected + deferred == full need.
    full = route_post(_urgent_signal(), RoutingConfig(max_workers=5))
    assert decision.selected_workers + decision.deferred_workers == (
        full.selected_workers
    )


def test_complexity_increases_budget_within_cap():
    simple = route_post(_low_signal(verification_complexity=0.1))
    complex_signal = route_post(_low_signal(verification_complexity=0.9))
    assert complex_signal.worker_budget >= simple.worker_budget
    assert complex_signal.worker_budget <= RoutingConfig().max_workers


def test_priority_is_not_truth_verdict():
    decision = route_post(_urgent_signal())
    payload = decision.to_dict()
    assert "is_false" not in payload
    assert "falsity" not in {k.lower() for k in payload}
    assert "verdict" not in {k.lower() for k in payload}
    assert "not a truth/falsity verdict" in decision.explanation
    assert not math.isnan(decision.priority_score)


def test_platform_metadata_is_passthrough():
    a = route_post(_low_signal(platform="x", platform_post_id="1"))
    b = route_post(_low_signal(platform="y", platform_post_id="2"))
    assert a.priority_score == b.priority_score
    assert a.tier == b.tier
