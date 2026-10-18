import re, time, json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

CSV = r"C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv"


def clean(t):
    if not isinstance(t, str):
        return ""
    t = re.sub(r"https?://\S+", " URL ", t)
    t = re.sub(r"@\w+", " USER ", t)
    t = re.sub(r"#\w+", " HASHTAG ", t)
    return re.sub(r"\s+", " ", t).strip()


df = pd.read_csv(CSV, low_memory=False)
df = df[df["label_binary"].notna()].copy()
df["label"] = df["label_binary"].astype(int)
df["text"] = (
    df["content_clean"].fillna("").astype(str) + " " + df["title"].fillna("").astype(str)
).map(clean)
df = df[df["text"].str.len() > 5].reset_index(drop=True)
df["source_dataset"] = df["source_dataset"].fillna("unknown").astype(str)
df["topic"] = df["topic"].fillna("unknown").astype(str)

print(f"rows: {len(df):,} | fake: {(df.label==1).sum():,} | real: {(df.label==0).sum():,}")

Xtr, Xte, ytr, yte = train_test_split(
    df[["text", "source_dataset", "topic"]],
    df["label"],
    test_size=0.2,
    random_state=42,
    stratify=df["label"],
)

prep = ColumnTransformer([
    ("text", TfidfVectorizer(max_features=15000, ngram_range=(1, 2), stop_words="english"), "text"),
    ("char", TfidfVectorizer(max_features=8000, ngram_range=(3, 5), analyzer="char"), "text"),
    ("meta", OneHotEncoder(handle_unknown="ignore", sparse_output=True), ["source_dataset", "topic"]),
], sparse_threshold=0.3, remainder="drop")

pipe = Pipeline([
    ("prep", prep),
    ("clf", LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced")),
])

t0 = time.time()
pipe.fit(Xtr, ytr)
pred = pipe.predict(Xte)
print("FIT seconds:", round(time.time() - t0, 1))
print("holdout_accuracy:", round(float(accuracy_score(yte, pred)), 4))
print("holdout_f1_fake:", round(float(f1_score(yte, pred, pos_label=1)), 4))
print("holdout_f1_real:", round(float(f1_score(yte, pred, pos_label=0)), 4))
print("confusion:", confusion_matrix(yte, pred).tolist())

md = Path(__file__).resolve().parents[1] / "models" / "fake_news_improved"
md.mkdir(parents=True, exist_ok=True)
joblib.dump(pipe, md / "pipeline.joblib")
json.dump({
    "holdout_accuracy": round(float(accuracy_score(yte, pred)), 4),
    "holdout_f1_fake": round(float(f1_score(yte, pred, pos_label=1)), 4),
    "holdout_f1_real": round(float(f1_score(yte, pred, pos_label=0)), 4),
    "model": "tfidf-logreg-char+meta",
}, open(md / "metrics.json", "w"), indent=1)
print("saved to", md)
