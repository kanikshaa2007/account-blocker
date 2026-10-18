# Stage6 - Dashboard + Runner Wiring (report-only)

## What was built
- `backend/app/services/eventbus/monitor_store.py` — singleton `MonitorStore`: jobs/reviews/actions, `approve()` records `report_platform` (never block).
- `backend/app/services/eventbus/wiring.py` — `make_callbacks()`: `start_simulation` queues `sim_{platform}_{post_id}` forecast request, `queue_report` stores job, `queue_review` stores review.
- `backend/app/api/monitor.py` — `GET /api/monitor/queue`, `POST /api/monitor/approve`.
- `backend/app/__init__.py` — registers `monitor_bp` + `realtime_bp`, additive try/except, baseline boot preserved.
- `frontend/src/api/monitor.js` + `frontend/src/views/MonitorView.vue` + router `/monitor` — jobs table, approve button, reviews list.
- `backend/tests/test_stage6_monitor.py` — wiring->queue->approve flow + realtime blueprint check.

## Verified
- Backend: 59 passed (`stage6+stage5+stage4+stage3+stage2+stage1+router`).
- Frontend: not built here (`vite` not installed; run `npm run setup` then `npm run build` from `frontend/`).

## Run
- Backend: `GET /api/monitor/queue`, dashboard at `/monitor`.
- Approve = draft platform report for human submission. No auto-block anywhere.
