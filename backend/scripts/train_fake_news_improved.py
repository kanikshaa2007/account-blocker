"""Improved fake-news classifier (fast config) on master_fake_real_clean.csv.
Improvements over baseline:
- Character n-grams + word n-grams TF-IDF
- Metadata features: source_dataset, topic, text length, word count
- Model comparison: LogisticRegression, LinearSVC, SGDClassifier
- Stratified 3-fold cross-validation
- Saves best model + metrics
CPU-only, ~1-2 min on 68k rows.
"""
import argparse
import json
import re
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix,
)

CSV_PATH = r"C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv"


def clean_text(t):
    if not isinstance(t, str):
        return ""
    t = re.sub(r"https?://\S+", " URL ", t)
    t = re.sub(r"@\w+", " USER ", t)
    t = re.sub(r"#\w+", " HASHTAG ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_and_prep(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df = df[df["label_binary"].notna()].copy()
    df["label"] = df["label_binary"].astype(int)
    df["text"] = (
        df["content_clean"].fillna("").astype(str) + " " +
        df["title"].fillna("").astype(str)
    ).map(clean_text)
    df = df[df["text"].str.len() > 5].reset_index(drop=True)
    df["source_dataset"] = df["source_dataset"].fillna("unknown").astype(str)
    df["topic"] = df["topic"].fillna("unknown").astype(str)
    df["char_count"] = df["char_count"].fillna(0).astype(float)
    df["word_count"] = df["word_count"].fillna(0).astype(float)
    print(f"rows: {len(df):,} | fake: {(df.label==1).sum():,} | real: {(df.label==0).sum():,}")
    return df


def build_pipeline(model_name, max_features):
    text_tfidf = TfidfVectorizer(
        max_features=max_features, ngram_range=(1, 2), analyzer="word",
        stop_words="english", strip_accents="unicode",
    )
    char_tfidf = TfidfVectorizer(
        max_features=10000, ngram_range=(3, 5), analyzer="char",
        strip_accents="unicode",
    )
    preprocess = ColumnTransformer(
        transformers=[
            ("text", text_tfidf, "text"),
            ("char", char_tfidf, "text"),
            ("meta", OneHotEncoder(handle_unknown="ignore", sparse_output=True),
             ["source_dataset", "topic"]),
            ("num", "passthrough", ["char_count", "word_count"]),
        ],
        sparse_threshold=0.3, remainder="drop",
    )
    if model_name == "logreg":
        clf = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced")
    elif model_name == "linearsvc":
        clf = LinearSVC(C=1.0, max_iter=2000, class_weight="balanced")
    elif model_name == "sgd":
        clf = SGDClassifier(loss="log_loss", alpha=0.0001, max_iter=2000,
                            class_weight="balanced", random_state=42)
    else:
        raise ValueError(f"unknown model {model_name}")
    return Pipeline([("preprocess", preprocess), ("clf", clf)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_PATH)
    ap.add_argument("--model-dir", default="models/fake_news_improved")
    ap.add_argument("--max-features", type=int, default=20000)
    ap.add_argument("--cv", type=int, default=3)
    args = ap.parse_args()

    df = load_and_prep(args.csv)
    X = df[["text", "source_dataset", "topic", "char_count", "word_count"]]
    y = df["label"]

    models = ["logreg", "linearsvc", "sgd"]
    results = []
    best = None
    best_f1 = -1.0

    for name in models:
        t0 = time.time()
        print(f"\n=== Training {name} ===")
        pipe = build_pipeline(name, args.max_features)
        cv = StratifiedKFold(n_splits=args.cv, shuffle=True, random_state=42)
        cv_results = cross_validate(
            pipe, X, y, cv=cv,
            scoring=["accuracy", "precision", "recall", "f1"],
            n_jobs=1, return_train_score=False,
        )
        res = {
            "model": name,
            "cv_accuracy_mean": round(float(cv_results["test_accuracy"].mean()), 4),
            "cv_accuracy_std": round(float(cv_results["test_accuracy"].std()), 4),
            "cv_precision_mean": round(float(cv_results["test_precision"].mean()), 4),
            "cv_recall_mean": round(float(cv_results["test_recall"].mean()), 4),
            "cv_f1_mean": round(float(cv_results["test_f1"].mean()), 4),
            "cv_f1_std": round(float(cv_results["test_f1"].std()), 4),
            "fit_seconds": round(time.time() - t0, 1),
        }
        results.append(res)
        print(json.dumps(res, indent=1))
        if res["cv_f1_mean"] > best_f1:
            best_f1 = res["cv_f1_mean"]
            best = (name, pipe)

    name, pipe = best
    print(f"\n=== Refit best model: {name} on full train ===")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    holdout = {
        "holdout_accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "holdout_precision_fake": round(float(precision_score(y_te, pred, pos_label=1)), 4),
        "holdout_recall_fake": round(float(recall_score(y_te, pred, pos_label=1)), 4),
        "holdout_f1_fake": round(float(f1_score(y_te, pred, pos_label=1)), 4),
        "holdout_precision_real": round(float(precision_score(y_te, pred, pos_label=0)), 4),
        "holdout_recall_real": round(float(recall_score(y_te, pred, pos_label=0)), 4),
        "holdout_f1_real": round(float(f1_score(y_te, pred, pos_label=0)), 4),
        "holdout_confusion_matrix": [[int(v) for v in row]
                                     for row in confusion_matrix(y_te, pred).tolist()],
    }
    print(json.dumps(holdout, indent=1))

    model_dir = Path(__file__).resolve().parents[1] / args.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_dir / "pipeline.joblib")
    report = {
        "best_model": name,
        "cv_results": results,
        "holdout": holdout,
        "columns": ["text", "source_dataset", "topic", "char_count", "word_count"],
    }
    (model_dir / "metrics.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("saved:", model_dir)


if __name__ == "__main__":
    raise SystemExit(main())
