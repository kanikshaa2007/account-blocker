"""ML classifier wrapper (Stage9): TF-IDF + LogReg trained on IFND + ISOT.

Conservative by design: the model only ever SUPPORTS a verdict.
confirmed_fake still requires an official citation; a high model score
without evidence keeps 'unverified' and says the model suspects fake.
Missing artifact -> returns None, never raises.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "fake_news_master"


@lru_cache(maxsize=1)
def _load():
    try:
        import joblib
    except ImportError:
        return None, None
    vec_path = MODEL_DIR / "vectorizer.joblib"
    mod_path = MODEL_DIR / "model.joblib"
    if not vec_path.exists() or not mod_path.exists():
        return None, None
    try:
        return joblib.load(vec_path), joblib.load(mod_path)
    except Exception:
        return None, None


def fake_probability(text: str) -> Optional[float]:
    """P(fake) in [0,1], or None when the model is unavailable/empty."""
    if not (text or "").strip():
        return None
    vec, clf = _load()
    if vec is None or clf is None:
        return None
    try:
        proba = clf.predict_proba(vec.transform([text]))[0]
        fake_idx = int(list(clf.classes_).index(1))
        return round(float(proba[fake_idx]), 4)
    except Exception:
        return None
