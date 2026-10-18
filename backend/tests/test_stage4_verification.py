"""Stage4 verification tests (isolated: no network)."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

_BASE = Path(__file__).resolve().parents[1] / "app" / "services" / "verification"


def _load(name):
    mod_name = f"stage4_test_{name}"
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_pib_scoring():
    pib = _load("pib_client")
    facts = [pib.FactCheck(external_id="1", title="PIB: viral UPI shutdown claim is fake", link="https://x/1")]
    best, score = pib.find_best_fact("viral Government of India UPI shutdown claim", facts)
    assert best is not None and score >= 0.3
    best2, _ = pib.find_best_fact("cute cat video", facts)
    assert best2 is None


def test_web_writer_extract():
    writer = _load("web_writer")
    html = "<html><head><title>PIB Fact Check</title></head><body><p>UPI shutdown is fake</p><script>evil()</script></body></html>"
    text = writer.extract_text(html)
    assert "UPI shutdown is fake" in text and "evil" not in text
    try:
        writer.fetch_evidence("ftp://x")
        assert False, "must reject non-http"
    except ValueError:
        pass


def test_verify_workers_verdict():
    workers = _load("workers")
    pib = _load("pib_client")
    facts = [pib.FactCheck(external_id="1", title="PIB: Aadhaar shutdown claim fake", link="https://factcheck/1")]
    result = workers.verify_claim(
        "Government of India Aadhaar shutdown viral claim", facts,
        content_type="video", language="hi",
        fetch_evidence=lambda url: SimpleNamespace(snippet="official denial text"),
    )
    assert result.verdict == "confirmed_fake"
    assert "video_forensics" in result.workers_run
    assert "multilingual_retriever" in result.workers_run
    assert "evidence_synthesizer" in result.workers_run
    assert result.citations == ["https://factcheck/1"]

    undecided = workers.verify_claim("random cat video", facts, content_type="text", language="en")
    assert undecided.verdict == "unverified"
    assert undecided.best_fact is None
