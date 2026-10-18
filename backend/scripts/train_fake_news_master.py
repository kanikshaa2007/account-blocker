"""Train fake-news classifier on the downloaded master_fake_real_clean.csv.

Label: label_binary == 1 -> fake, == 0 -> real (drops Bias/Satire rows).
Text: content_clean + title.
Saves: backend/models/fake_news_master/ (vectorizer.joblib, model.joblib, metrics.json).
CPU-only, ~1-2 min on 68k rows.
"""
import argparse
import json
import re
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

CSV_PATH = r"C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv"


def clean_text(t):
    if not isinstance(t, str):
        return ""
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_PATH)
    ap.add_argument("--model-dir", default="models/fake_news_master")
    ap.add_argument("--max-features", type=int, default=60000)
    ap.add_argument("--C", type=float, default=1.0)
    args = ap.parse_args()

    t0 = time.time()
    df = pd.read_csv(args.csv, low_memory=False)

    # Binary labels only: 1 = fake, 0 = real; drop Bias/Satire (NaN)
    df = df[df["label_binary"].notna()].copy()
    df["label"] = df["label_binary"].astype(int)
    df["text"] = (df["content_clean"].fillna("") + " " + df["title"].fillna("")).map(clean_text)
    df = df[df["text"].str.len() > 5]

    print(f"rows: {len(df):,} | fake: {(df.label==1).sum():,} | real: {(df.label==0).sum():,}")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    vec = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2),
                          stop_words="english", strip_accents="unicode")
    Xtr = vec.fit_transform(X_train)
    Xte = vec.transform(X_test)

    clf = LogisticRegression(C=args.C, max_iter=1000, n_jobs=-1)
    clf.fit(Xtr, y_train)
    pred = clf.predict(Xte)

    metrics = {
        "train_n": int(len(df)),
        "fake_n": int((df.label == 1).sum()),
        "real_n": int((df.label == 0).sum()),
        "test_n": int(len(y_test)),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision_fake": round(float(precision_score(y_test, pred, pos_label=1)), 4),
        "recall_fake": round(float(recall_score(y_test, pred, pos_label=1)), 4),
        "f1_fake": round(float(f1_score(y_test, pred, pos_label=1)), 4),
        "precision_real": round(float(precision_score(y_test, pred, pos_label=0)), 4),
        "recall_real": round(float(recall_score(y_test, pred, pos_label=0)), 4),
        "f1_real": round(float(f1_score(y_test, pred, pos_label=0)), 4),
        "confusion_matrix": [[int(v) for v in row] for row in confusion_matrix(y_test, pred).tolist()],
        "model": "tfidf-logreg", "C": args.C, "max_features": args.max_features,
        "seconds": round(time.time() - t0, 1),
    }
    print(json.dumps(metrics, indent=1))

    model_dir = Path(__file__).resolve().parents[1] / args.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vec, model_dir / "vectorizer.joblib")
    joblib.dump(clf, model_dir / "model.joblib")
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    print("saved:", model_dir)


if __name__ == "__main__":
    raise SystemExit(main())
