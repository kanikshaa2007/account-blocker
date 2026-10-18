"""PIB ground-truth client (Stage4): RSS -> fact-check index, offline-testable."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class FactCheck:
    external_id: str
    title: str
    link: str
    published: str = ""


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def score_claim_vs_fact(claim: str, fact_title: str) -> float:
    """Overlap score 0-1: shared informative tokens / claim tokens."""
    stop = {"the", "a", "an", "of", "in", "on", "is", "to", "for", "and", "govt", "government"}
    claim_toks = _tokens(claim) - stop
    fact_toks = _tokens(fact_title) - stop
    if not claim_toks or not fact_toks:
        return 0.0
    return round(len(claim_toks & fact_toks) / max(1, len(claim_toks)), 4)


def find_best_fact(claim: str, facts: List[FactCheck], min_score: float = 0.3) -> tuple[FactCheck | None, float]:
    best: FactCheck | None = None
    best_score = 0.0
    for fact in facts:
        score = score_claim_vs_fact(claim, fact.title)
        if score > best_score:
            best_score = score
            best = fact
    if best is None or best_score < min_score:
        return None, round(best_score, 4)
    return best, round(best_score, 4)
