# Stage7 - Live Dry-Run (real chain, no blocking)

Run: `python scripts/stage7_dryrun.py` from `backend/`.

## Result (2026-10-16)
- Keys: `NEO4J_URI/USER`, `PIB_FACTCHECK_RSS_URL`, `ACTION_MODE` SET; `LLM/ZEP` placeholders; `X/Instagram/YouTube` tokens + `NEO4J_PASSWORD` + webhook token MISSING.
- Neo4j: UNREACHABLE (no server on bolt://localhost:7687, expected). Store runs disabled, no writes lost.
- Full chain on 3 synthetic posts:
  - `x:x100` tier=normal fake, no burst -> no trigger (correct, avoids noise).
  - `instagram:ig200` tier=high fake, no burst -> no trigger.
  - `x:x999` off-topic skipped.
- Forced burst proof: urgent/high+burst+fake -> trigger=True, 1 job queued.
- Scheduler proof: `run_once` collected 2/2, stats show per-source counts + dedup.
- Blocking: NONE (report-only). Live API keys: NOT READY.

## To go live
1. Fill `.env`: real `LLM_API_KEY`, `ZEP_API_KEY`, `NEO4J_PASSWORD`, `X_BEARER_TOKEN`, `INSTAGRAM_ACCESS_TOKEN`, `YOUTUBE_API_KEY`.
2. Start Neo4j (`bolt://localhost:7687`), re-run script -> expect REACHABLE.
3. Expose `/api/realtime/*` webhooks, subscribe Instagram/YouTube push.
4. Start `RealtimeCollector.start_background()` + open `/monitor` to review.

## Tests
- 59 passed (all stage suites + Flask monitor API).
