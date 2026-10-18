"""Stage9 model tests (fast: tiny in-memory fit + artifact-missing grace)."""
import importlib.util
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "verification"


def _load(name):
    mod_name = f"stage9_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_model_verifier_graceful_without_artifact(tmp_path, monkeypatch):
    model_verifier = _load("model_verifier")
    monkeypatch.setattr(model_verifier, "MODEL_DIR", tmp_path / "missing")
    model_verifier._load.cache_clear()
    try:
        assert model_verifier.fake_probability("some claim") is None
        assert model_verifier.fake_probability("   ") is None
    finally:
        model_verifier._load.cache_clear()


def test_model_supports_but_never_decides():
    workers = _load("workers")
    pib = _load("pib_client")
    facts = [pib.FactCheck(external_id="1", title="PIB: UPI shutdown claim fake", link="https://x/1")]

    # Citation + high model score -> confirmed_fake with ml worker listed.
    r = workers.verify_claim("UPI shutdown claim", facts, ml_fake_prob=0.95)
    assert r.verdict == "confirmed_fake"
    assert "ml_classifier" in r.workers_run
    assert r.ml_fake_prob == 0.95

    # High model score alone -> still unverified, suspicion noted.
    r2 = workers.verify_claim("something entirely different here xyz", facts, ml_fake_prob=0.95)
    assert r2.verdict == "unverified"
    assert "suspects fake" in r2.reason


def test_tiny_model_trains_and_predicts(tmp_path):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    texts = ["upi shutdown fake viral forward", "rbi bans notes rumor fake",
             "parliament passes budget bill today", "census data released by ministry"]
    labels = [1, 1, 0, 0]
    vec = TfidfVectorizer()
    clf = LogisticRegression(max_iter=1000).fit(vec.fit_transform(texts), labels)
    proba = clf.predict_proba(vec.transform(["viral forward claims upi shutdown fake"]))[0]
    assert proba[int(list(clf.classes_).index(1))] > 0.5
