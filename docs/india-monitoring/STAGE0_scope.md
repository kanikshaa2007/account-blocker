# Stage0 - Baseline Freeze + Scope + Compliance (India Viral Monitoring)

## 1. Baseline frozen
- MiroFish core unchanged: Flask `backend/app` (graph/simulation/report blueprints), Vue3 frontend, OASIS twitter/reddit, Zep Cloud memory.
- Python 3.11.9 OK (requires >=3.11,<3.13). Node v24.15.0 OK (>=18).
- `backend/requirements.txt` adds only `neo4j>=5.23.0` (already present transitively in `uv.lock` via camel). No other dependency change in Stage0.

## 2. Scope (gov-of-India fake-news triage, report-only)
- IN SCOPE: X + Instagram + YouTube public viral posts mentioning gov schemes/ministries, PIB Fact Check as ground truth, Neo4j spread topology, `moderation/router.py:route_post` urgency tiers, OASIS forecast, reviewer dashboard.
- OUT OF SCOPE (Stage0): auto-block/mute of any third-party account, login-wall scraping, WhatsApp/Telegram private data, fully automated takedown.

## 3. Ground truth
- Primary: PIB Fact Check (`PIB_FACTCHECK_RSS_URL`), pib.gov.in press releases, ministry handles. Web-Writer (browser automation) reads public pages only, stores URL + snapshot + timestamp as evidence.
- Rule: `confirmed_fake` requires >=1 official citation. Else `unverified`.

## 4. Compliance guardrails
- Official APIs only: X API v2 (`X_BEARER_TOKEN`), Instagram Graph API (`INSTAGRAM_ACCESS_TOKEN`), YouTube Data API (`YOUTUBE_API_KEY`). Respect ToS/rate limits/robots.
- `ACTION_MODE=report_only` enforced by `Config.validate_stage0()`. Any other value emits warning and must not proceed to action.
- Virality != guilt: `router.py` score is verification urgency only. Human reviewer approves all quarantine/report/escalate actions. Audit log required (who, what, evidence URLs).
- PII minimization: store post IDs + public metrics, not passwords or private messages.

## 5. Config
- See `.env.example` Stage0 block + `backend/app/config.py:Config` new fields (`NEO4J_*`, `X_BEARER_TOKEN`, `INSTAGRAM_ACCESS_TOKEN`, `YOUTUBE_API_KEY`, `PIB_FACTCHECK_RSS_URL`, `ACTION_MODE`).
- `validate()` unchanged (baseline boot behavior). `validate_stage0()` is warn-only, never blocks boot.

## 6. Exit criteria
- [x] `.env.example` has Stage0 block
- [x] `Config.validate_stage0()` reports missing-connector warnings, not errors
- [ ] `cp .env.example .env` done by operator + keys filled
- [ ] `python -c "from app.config import Config; print(Config.validate_stage0())"` runs clean
- Next: Stage1 connectors (X/Instagram/YouTube -> RoutingInput).
