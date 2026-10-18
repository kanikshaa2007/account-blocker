# Stage2 - Spread Graph (Neo4j) + Analytics

## What was built
- `backend/app/services/spread_graph/schema.py` — constraints/indexes + Cypher: `UPSERT_POST`, `RECORD_VELOCITY`, `FOLLOW_EDGE`, `SUPERSPREADERS_FALLBACK`, `BURST_POSTS`.
  - Graph: `(:Account)-[:POSTED]->(:Post)-[:HAS_CLAIM]->(:Claim)`, `(:Post)-[:HAS_VELOCITY]->(:VelocitySnapshot)`.
- `backend/app/services/spread_graph/analytics.py` — pure functions: `detect_burst(history)`, `pagerank(edges)`, `spread_score(posts, engagement, followers)`.
- `backend/app/services/spread_graph/store.py` — `Neo4jStore` (driver-injectable):
  - Missing `NEO4J_PASSWORD` and no injected driver => `enabled=False`, all writes no-op, reads `[]`. Never blocks boot.
  - `ensure_schema/upsert_post/record_velocity/add_follow/superspreaders/burst_posts/to_zep_payload`.
- `backend/tests/test_stage2_spread_graph.py` — fake-driver flow, disabled-mode, burst/PageRank math.

## Verified
- `pytest test_stage2 + test_stage1 + test_moderation_router` — 46 passed.

## Next (Stage3)
- `event_bus.py`: `high/urgent + burst` -> `SimulationManager.create+prepare` + ReportAgent. Human approves all actions (`report_only`).
