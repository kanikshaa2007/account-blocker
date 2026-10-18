"""Train fake-news classifier: IFND train + ISOT train -> TF-IDF + LogReg.

Label convention (verified by sampling): 1 = fake, 0 = real in both datasets.
Saves vectorizer + model (joblib) and metrics JSON. CPU-only, minutes.
"""
import argparse
import json
import time
from pathlib import Path

from datasets import load_dataset, concatenate_datasets
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import joblib


def as_binary_ifnd(ds):
    texts = [(r["text"] or "") for r in ds]
    labels = [int(r["label"]) for r in ds]
    return texts, labels


def as_binary_isot(ds):
    texts = [(r["text"] or "") for r in ds]
    labels = [int(r["target"]) for r in ds]
    return texts, labels


def metrics(name, y_true, y_pred):
    m = {"n": len(y_true),
         "accuracy": round(accuracy_score(y_true, y_pred), 4),
         "precision_fake": round(precision_score(y_true, y_pred, zero_division=0), 4),
         "recall_fake": round(recall_score(y_true, y_pred, zero_division=0), 4),
         "f1_fake": round(f1_score(y_true, y_pred, zero_division=0), 4)}
    print(name, m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="models/fake_news_tfidf")
    ap.add_argument("--max-features", type=int, default=50000)
    ap.add_argument("--C", type=float, default=1.0)
    args = ap.parse_args()

    t0 = time.time()
    ifnd_train = load_dataset("Nhat243/IFND-multimodal", split="train").remove_columns(["image"])
    isot_train = load_dataset("Phoenyx83/ISOT-Fake-News-Dataset-FineTuned-2022", split="train")
    X_text, y = as_binary_ifnd(ifnd_train)
    tx2, y2 = as_binary_isot(isot_train)
    X_text += tx2
    y += y2
    print(f"train rows: {len(y)} (IFND {len(ifnd_train)} + ISOT {len(isot_train)})")

    vec = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2),
                          stop_words="english", strip_accents="unicode")
    X = vec.fit_transform(X_text)
    clf = LogisticRegression(C=args.C, max_iter=1000)
    clf.fit(X, y)

    report = {"train_n": len(y), "model": "tfidf-logreg", "C": args.C,
              "max_features": args.max_features, "splits": {}}
    ifnd_valid = load_dataset("Nhat243/IFND-multimodal", split="validation").remove_columns(["image"])
    ifnd_test = load_dataset("Nhat243/IFND-multimodal", split="test").remove_columns(["image"])
    isot_valid = load_dataset("Phoenyx83/ISOT-Fake-News-Dataset-FineTuned-2022", split="validation")
    for name, ds, fn in (("ifnd_valid", ifnd_valid, as_binary_ifnd),
                         ("ifnd_test", ifnd_test, as_binary_ifnd),
                         ("isot_validation", isot_valid, as_binary_isot)):
        texts, labels = fn(ds)
        pred = clf.predict(vec.transform(texts))
        report["splits"][name] = metrics(name, labels, pred)

    model_dir = Path(__file__).resolve().parents[1] / args.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vec, model_dir / "vectorizer.joblib")
    joblib.dump(clf, model_dir / "model.joblib")
    report["seconds"] = round(time.time() - t0, 1)
    (model_dir / "metrics.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("saved:", model_dir, f"({report['seconds']}s)")


if __name__ == "__main__":
    raise SystemExit(main())
