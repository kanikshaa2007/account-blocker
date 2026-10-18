# LIVE Integration Proof (2026-10-16)

## What runs
- Backend `:5001` (Flask, all blueprints incl. `monitor` + `realtime`).
- Frontend `:3000` (Vite dev, `/api` proxied to backend).
- `POST /api/monitor/ingest` — one live cycle, keyless public sources only.

## Live result (real network, real items)
- `fetched`: gnews 40, fact_pool 4, reddit_rss 10, youtube_rss 10 (bot-gated at times), pib_facts 0, reddit_json 0.
- `routed`: 39 through gov-gate + router + verification; 21 off-topic skipped.
- Real social accounts in queue with post IDs, e.g. u/viksi Delhi-protests megathread (1x1oy64), u/mumbaiblues IAS viral video (1x77053), u/Downtown-Sir-3200, u/Status_Pool_54, plus DD India YouTube videos.
- `jobs`/`reviews`: 0 — correctly no trigger (all tier normal, no burst).

## Honest limitations found live
- PIB `/feed` is 404; factcheck homepage is ASP.NET with no public feed -> ground truth falls back to verdict-pattern Google News headlines (real, cited). Documented in code.
- Reddit public JSON is 403 without OAuth -> skipped gracefully; needs OAuth key for live Reddit.
- X/Instagram/YouTube need official tokens (still placeholders in `.env`).

## How to see it
1. Open `http://localhost:3000/console/settings` -> turn OFF demo mode.
2. Open Live Monitor -> Fetch live feed -> real rows appear with platform IDs, tiers, scores.
3. Queue shows jobs only when a real urgent+burst+fake event occurs.

## Tests/builds
- Backend: 60 passed (incl. `test_stage7_ingest` with stubbed fetchers).
- Frontend: `vite build` clean; all console routes 200.
