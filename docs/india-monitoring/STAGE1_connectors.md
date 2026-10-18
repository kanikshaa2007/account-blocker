# Stage1 - Connectors: X / Instagram / YouTube -> RoutingInput

## What was built
- `backend/app/services/connectors/models.py` — `NormalizedPost` (platform, post_id, text, author, followers, lang, content_type, likes/shares/comments/views, url).
- `backend/app/services/connectors/gov_topics.py` — `mentions_gov()` gate (PMO/ECI/RBI/UPI/Aadhaar/PM-KISAN/etc). Off-topic posts are skipped, never routed.
- `backend/app/services/connectors/clients.py` — official APIs only, token-lazy, missing token returns `[]`:
  - `fetch_x_recent(query)` — X API v2 recent search (bearer).
  - `fetch_instagram_hashtag(hashtag_id, user_id)` — Instagram Graph API recent_media.
  - `fetch_youtube_search(query)` — YouTube Data API v3 search.
  - Pure `parse_*` helpers for tests/offline.
- `backend/app/services/connectors/scoring.py` — `spread_velocity()` + `to_routing_input()`:
  - `velocity = 0.5*reshare_rate + 0.3*follower_amp + 0.2*cross_platform`, clamped 0-1.
  - No engagement signal => `(0.0, reliable=False)` so `router.py` uses fallback estimate.
  - `harm=0.7 (+0.15 video/mixed)`, `complexity=0.6 video/audio/mixed else 0.3`, `uncertainty default 0.7`.
- `backend/app/services/connectors/collector.py` — `collect_all()` gather -> gov-gate -> `RoutingInput`. `fetch=` injection for tests.
- `backend/tests/test_stage1_connectors.py` — offline parsers, gov-gate, scoring, collector skip logic.

## Verified
- `pytest tests/test_stage1_connectors.py tests/test_moderation_router.py` — 43 passed.
- Missing tokens safely skip (Stage0 warn-only behavior preserved).

## Next (Stage2)
- `neo4j_store.py`: upsert `(:Account)-[:POSTED]->(:Post)-[:HAS_CLAIM]->(:Claim)`, velocity history, PageRank super-spreaders.
