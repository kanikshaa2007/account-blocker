"""HF IFND test: pipeline behavior on real Indian news text (offline, cached dataset).

Measures, honestly framed:
  A. Gate: pass rate per label group (gov-relevance triage, not truth).
  B. Router: tier distribution per group (urgency, not falsity).
  C. Matcher: label=0 items DESCRIBE false claims ("X is fake"). Split them:
     facts from half A, verify claims from half B -> confirmed_fake recall.
     Label=1 plain news verified against same facts -> false-trigger rate.
"""
import importlib.util
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load(mod_path, name):
    spec = importlib.util.spec_from_file_location(name, BACKEND / mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(n_per_group=246, seed=7):
    from datasets import load_dataset
    scoring = load("app/services/connectors/scoring.py", "hf_scoring")
    route_post = scoring._router.route_post
    pib = load("app/services/verification/pib_client.py", "hf_pib")
    workers = load("app/services/verification/workers.py", "hf_workers")

    ds = load_dataset("Nhat243/IFND-multimodal", split="test").remove_columns(["image"])
    rng = random.Random(seed)
    grp0 = [r for r in ds if r["label"] == 0]
    grp1_all = [r for r in ds if r["label"] == 1]
    grp1 = rng.sample(grp1_all, min(n_per_group, len(grp1_all)))
    print(f"group0 debunk-style: {len(grp0)}, group1 plain-news sample: {len(grp1)}")

    def to_post(row, idx):
        return SimpleNamespace(platform="ifnd", platform_post_id=f"ifnd-{idx}",
                               text=row["text"] or "", author_id="ifnd", author_followers=0,
                               language="en", content_type="text", likes=0, shares=0,
                               comments=0, views=0, created_at="", url="")

    stats = {}
    gated = {}
    for gname, rows in (("label0", grp0), ("label1", grp1)):
        passed, tiers = [], {"low": 0, "normal": 0, "high": 0, "urgent": 0}
        for i, row in enumerate(rows):
            try:
                signal = scoring.to_routing_input(to_post(row, i))
            except ValueError:
                continue
            decision = route_post(signal)
            passed.append((row, signal, decision))
            tiers[decision.tier] += 1
        gated[gname] = passed
        stats[gname] = {"n": len(rows), "gated": len(passed),
                        "gate_rate": round(len(passed) / max(1, len(rows)), 3), "tiers": tiers}
        print(gname, stats[gname])

    # Matcher test: facts from half of label0, verify rest of label0 + label1 sample.
    half = len(gated["label0"]) // 2
    facts = [pib.FactCheck(external_id=f"ifnd-f{i}", title=r[0]["text"][:300], link=f"ifnd://{i}")
             for i, r in enumerate(gated["label0"][:half])]
    print(f"fact pool: {len(facts)} (from label0 half A)")

    def verify_rate(items):
        hits = sum(1 for r, _, _ in items
                   if workers.verify_claim(r["text"], facts, min_score=0.3).verdict == "confirmed_fake")
        return {"n": len(items), "confirmed_fake": hits,
                "rate": round(hits / max(1, len(items)), 3)}

    recall = verify_rate(gated["label0"][half:])
    fpr = verify_rate(gated["label1"])
    print("label0-halfB recall:", recall)
    print("label1 false-trigger:", fpr)

    report = {"gate_router": stats, "matcher_recall_label0": recall,
              "matcher_false_trigger_label1": fpr}
    out = BACKEND.parent / "docs" / "india-monitoring" / "HF_IFND_test.md"
    out.write_text("# HF IFND Test (Nhat243/IFND-multimodal, test split)\n\n```json\n" +
                   json.dumps(report, indent=1) + "\n```\n", encoding="utf-8")
    print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
