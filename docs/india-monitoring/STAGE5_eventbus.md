# Stage5 - Event Bus (urgent+burst+fake -> simulate, report-only)

## What was built
- `backend/app/services/eventbus/bus.py` — `BusEvent`, `should_trigger()`, `EventBus.emit()`:
  - `high/urgent + burst + confirmed_fake` -> simulation + report jobs queued.
  - `high/urgent + burst + unverified` -> review queue only, no auto-sim.
  - Else no-op. `ACTION_MODE != report_only` raises, never blocks accounts.
- `backend/tests/test_stage5_eventbus.py` — trigger, review-only, low-tier, job queue, mode guard.

## Verified
- 57 passed (`stage5+stage4+stage3+stage2+stage1+router`), offline.

## Next (Stage6)
- Reviewer dashboard queue + `simulation_runner` wiring + report API. Still report-only.
