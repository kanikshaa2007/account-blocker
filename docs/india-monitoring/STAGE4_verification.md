# Stage4 - Verification (PIB ground truth + Web-Writer + workers)

## What was built
- `backend/app/services/verification/pib_client.py` — `FactCheck`, `score_claim_vs_fact()`, `find_best_fact(min_score=0.3)`.
- `backend/app/services/verification/web_writer.py` — `fetch_evidence(url)` (public http(s) only) + `extract_text()` (strips script/style). Playwright can replace fetch later.
- `backend/app/services/verification/workers.py` — `verify_claim()`:
  - workers mirror router: `text_verifier` + `image/video_forensics` + `source_credibility` + `multilingual_retriever` + `evidence_synthesizer`.
  - `confirmed_fake` requires official PIB match >= threshold; else `unverified`, human review required.
- `backend/tests/test_stage4_verification.py` — scoring, extract, verdict paths.

## Verified
- 52 passed (`stage4+stage3+stage2+stage1+router`), offline.

## Next (Stage5)
- `event_bus.py`: `tier high/urgent + burst + confirmed_fake` -> OASIS `SimulationManager` forecast. Report-only.
