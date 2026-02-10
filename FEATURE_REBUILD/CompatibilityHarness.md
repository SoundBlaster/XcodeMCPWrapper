# Web UI Rebuild Compatibility Harness

## What Must Match (MUST list)

1. `/api/metrics` key set and value types used by dashboard remain unchanged.
2. `/api/metrics/timeseries` returns `{requests, errors, latencies}` arrays of `{t, v}`.
3. `/api/audit` pagination/filter behavior remains stable.
4. `/api/audit/export/json` and `/api/audit/export/csv` remain downloadable with valid payloads.
5. Non-auth mode dashboard continues to show live metrics via websocket or polling fallback.
6. Wrapper behavior without `--web-ui` remains unchanged.

## What May Change (MAY list)

1. Internal module boundaries and abstractions.
2. Internal storage query implementation details.
3. Error message wording, provided status codes and actionable guidance remain equivalent.

## Golden Sources (tests/fixtures/snapshots/logs)

- Test suites:
  - `tests/unit/webui/test_server.py`
  - `tests/unit/webui/test_shared_metrics.py`
  - `tests/integration/webui/test_e2e.py`
  - `tests/unit/test_main.py`
- Planned fixtures:
  - `tests/fixtures/webui/metrics_summary.json`
  - `tests/fixtures/webui/metrics_timeseries.json`
  - `tests/fixtures/webui/audit_page.json`
- Historical evidence:
  - `SPECS/INPROGRESS/Web_UI_Debugging_Summary.md`
  - `SPECS/ARCHIVE/P10-T2_Fix_Web_UI_Timeseries_Charts/P10-T2_Validation_Report.md`

## Parity Check Plan (how we compare)

1. API schema parity
   - Compare runtime responses against fixture schemas for required keys/types.
2. Behavior parity
   - Replay request/response tracking scenario; assert summary counters and in-flight transitions.
3. Timeseries parity
   - Assert chart payload format and bounded `t` range.
4. Audit parity
   - Assert filter/pagination/export output shape and ordering.
5. Auth parity
   - Assert protected endpoints return `401` without credentials and success with valid credentials.
6. Non-WebUI parity
   - Run core wrapper tests without `--web-ui`; assert no behavior deltas.

## CI Integration

- Add compatibility harness to CI quality gate for Web UI touching changes:
  - `pytest tests/integration/webui/test_compat_harness.py -v`
  - `pytest tests/unit/webui/ tests/integration/webui/ -v`
- Keep existing global checks:
  - `pytest`
  - `ruff check src/ tests/`
  - `mypy src/`

## Rollback Strategy

- Deployment model: single PR rollout with immediate revert path.
- Rollback trigger:
  - API contract mismatch, auth regression, or chart data regression in harness.
- Rollback action:
  1. Revert rebuild commit set.
  2. Re-run baseline Web UI test suites.
  3. Restore last known good release notes and docs references.
