"""Verification workers -> verdict (Stage4, pure + injectable).

Verdict rule (conservative):
- confirmed_fake requires >=1 official PIB/ministry citation with match >= threshold.
- confirmed_true requires official denial-of-rumor absence? Never auto-true on viral alone -> default unverified.
- Workers list mirrors moderation/router SUPPORTED_WORKERS naming.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

try:
    from .pib_client import FactCheck, find_best_fact
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

    _pib = _load("pib_client")
    FactCheck = _pib.FactCheck
    find_best_fact = _pib.find_best_fact


@dataclass(frozen=True)
class VerifyResult:
    verdict: str  # confirmed_fake | unverified | confirmed_true
    confidence: float
    best_fact: Optional[FactCheck]
    match_score: float
    workers_run: List[str]
    citations: List[str] = field(default_factory=list)
    reason: str = ""
    ml_fake_prob: Optional[float] = None


def verify_claim(
    claim_text: str,
    facts: List[FactCheck],
    content_type: str = "text",
    language: Optional[str] = None,
    min_score: float = 0.3,
    fetch_evidence: Callable[[str], object] | None = None,
    ml_fake_prob: Optional[float] = None,
) -> VerifyResult:
    workers = ["text_verifier"]
    if content_type in ("image", "mixed"):
        workers.append("image_forensics")
    if content_type in ("video", "mixed"):
        workers.append("video_forensics")
    if content_type == "audio":
        workers.append("audio_transcriber")
    workers.append("source_credibility")
    if language and language.lower() != "en":
        workers.append("multilingual_retriever")
    if ml_fake_prob is not None:
        workers.append("ml_classifier")

    best, score = find_best_fact(claim_text, facts, min_score=min_score)
    citations: List[str] = []
    if best is not None and fetch_evidence is not None:
        try:
            evidence = fetch_evidence(best.link)
            snippet = getattr(evidence, "snippet", "") or ""
            if snippet:
                workers.append("evidence_synthesizer")
            citations.append(best.link)
        except Exception:
            citations.append(best.link)
    elif best is not None:
        citations.append(best.link)

    if best is not None:
        confidence = min(0.95, 0.55 + score * 0.4)
        reason = f"Matched official fact-check '{best.title}' score={score}."
        if ml_fake_prob is not None:
            # Model supports, never decides: small confidence nudge either way.
            confidence = round(min(0.97, confidence + 0.1 * ml_fake_prob - 0.05), 4)
            reason += f" ML classifier P(fake)={ml_fake_prob}."
        verdict: Dict[str, object] = {"label": "confirmed_fake", "confidence": confidence}
    else:
        verdict = {"label": "unverified", "confidence": 0.35}
        reason = f"No official PIB match above {min_score} (best={score}). Human review required."
        if ml_fake_prob is not None and ml_fake_prob >= 0.85:
            reason += f" ML classifier suspects fake (P={ml_fake_prob}); official evidence still required."
    return VerifyResult(
        verdict=str(verdict["label"]), confidence=float(verdict["confidence"]),
        best_fact=best, match_score=score, workers_run=workers,
        citations=citations, reason=reason, ml_fake_prob=ml_fake_prob,
    )
