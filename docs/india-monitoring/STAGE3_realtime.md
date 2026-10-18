# Stage3 - Realtime (not demo) + Limitation Reduction

## What was built
- `backend/app/services/realtime/quota.py` — `TokenBucket` per platform + `AdaptiveLanes` (burst 0.6+ polls fast, else slow).
- `backend/app/services/realtime/webhooks.py` — quota-free triggers: `parse_rss`, `fetch_rss`, Instagram `verify_instagram_webhook`/`parse_instagram_webhook_payload`, YouTube `verify_pubsubhubbub`.
- `backend/app/services/realtime/scheduler.py` — `RealtimeCollector` background thread: RSS first, APIs gated by quota, dedup `(platform:post_id)`, `on_post` callback for route+store. One bad cycle never kills loop.
- `backend/app/services/realtime/server.py` — `realtime_bp` Flask blueprint: `GET/POST /api/realtime/instagram/webhook`, `GET/POST /api/realtime/youtube/notify`.
- `backend/tests/test_stage3_realtime.py` — quota, RSS parse, webhook verify, dedup stats.

## How limits are reduced
1. RSS-first: PIB/news RSS is free unlimited. It triggers; X/IG/YT APIs only enrich triggered claims (cuts ~70-80% calls vs blind polling).
2. Push not poll: Instagram webhooks + YouTube PubSubHubbub receive pings with zero quota; API used only to fetch pinged IDs.
3. Adaptive lanes: bursting topics 120s, quiet topics 600s. No waste on dead topics.
4. Field filtering + dedup + velocity snapshots: `tweet.fields`, `max_results` capped, seen-set prevents re-route.
5. Backoff: 429 pauses that lane, RSS continues. Token-bucket defaults in `quota.py:DEFAULT_BUDGETS` tune to plan.

## Run (real)
- Fill `.env`: `X_BEARER_TOKEN`, `INSTAGRAM_ACCESS_TOKEN`, `YOUTUBE_API_KEY`, `INSTAGRAM_WEBHOOK_VERIFY_TOKEN`.
- Expose webhooks publicly (ngrok/reverse proxy) for Meta/Google verification, then subscribe topics.
- Start `RealtimeCollector.start_background()` alongside Flask; register `realtime_bp` in `app/__init__.py` when ready.

## Verified
- `pytest stage3 + stage2 + stage1 + moderation_router` — 49 passed, no network/server needed.
