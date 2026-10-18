# Stage9 - Fake-News Classifier (trained on downloaded dataset)

## Dataset
`C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv` — 68,173 rows merged from ISOT, LIAR, TheOnion, MultiClass1, Propaganda, NotTheOnion_Reddit, Twitter, India_MythFacts.
- Columns: title, content, content_clean, label_binary (1=fake/0=true), label_text (Fake/True/Bias/Satire), source_dataset, topic, speaker, date, url.
- Binary training used label_binary only → 54,002 rows (24,205 fake / 29,797 real); Bias/Satire dropped.

## Training
`backend/scripts/train_fake_news_master.py` — TF-IDF word 1-2grams (60k feats, english stopwords) + LogisticRegression C=1.0, 80/20 stratified split. CPU 72s.

## Test results (held-out 20%)
| metric | value |
|---|---|
| accuracy | 0.8981 |
| precision (fake) | 0.9003 |
| recall (fake) | 0.8688 |
| F1 (fake) | 0.8843 |
| precision (real) | 0.8964 |
| recall (real) | 0.9218 |
| F1 (real) | 0.9089 |
| confusion matrix | [[5494, 466], [635, 4206]] |

## Artifact
`backend/models/fake_news_master/` — vectorizer.joblib, model.joblib, metrics.json.
`backend/app/services/verification/model_verifier.py` loads it via `fake_probability(text)` → P(fake) in [0,1], None if missing.

## Integration (conservative — model supports, never decides)
`verification/workers.verify_claim(..., ml_fake_prob=...)`:
- adds `ml_classifier` worker
- small confidence nudge on confirmed_fake citations
- high score alone → `unverified` with suspicion noted
- never auto-blocks

## Sanity probes
- "Parliament passes budget bill..." → 0.14 (real)
- "Prime Minister inaugurates new metro line..." → 0.13 (real)
- "PM-KISAN installment blocked..." → 0.43 (suspicious)
- "RBI bans Rs 500 notes again..." → 0.38 (suspicious)

## Tests
65 passed including `test_stage9_model` (tiny in-memory fit, missing-artifact grace, support-never-decides).
