# Validation Report: BUG-T12

**Task:** BUG-T12 — Audit Log does not show new calls  
**Date:** 2026-02-20  
**Branch:** feature/BUG-T12-audit-log-does-not-show-new-calls

## Summary

Implemented a dashboard-side audit refresh fix so new audit entries appear promptly during live traffic by:
- Triggering audit reloads from live `metrics_update` events when `total_requests` changes.
- Disabling browser cache for `/api/audit` fetches and appending a timestamp query param.
- Ignoring stale in-flight audit fetch responses to prevent old payloads from overwriting newer rows.

## Files Changed

- `src/mcpbridge_wrapper/webui/static/dashboard.js`
- `tests/unit/webui/test_server.py`

## Acceptance Criteria

- [x] New tool calls appear in the Audit Log table during an active dashboard session.
- [x] `/api/audit` returns newly created entries after calls complete.
- [x] Existing audit row-state behavior regressions are not reintroduced.
- [x] Targeted regression tests added/updated and passing.
- [x] Full quality gates pass (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with >=90% coverage).

## Quality Gates

1. `PYTHONPATH=src pytest tests/unit/webui/test_server.py -q`  
   Result: **PASS** (42 passed)

2. `PYTHONPATH=src ruff check src/`  
   Result: **PASS** (All checks passed)

3. `PYTHONPATH=src mypy src/`  
   Result: **PASS** (Success: no issues found in 18 source files)

4. `PYTHONPATH=src pytest`  
   Result: **PASS** (633 passed, 5 skipped)

5. `PYTHONPATH=src pytest --cov`  
   Result: **PASS** (coverage 91.33%, threshold >= 90%)

## Notes

- Existing warnings from `websockets.legacy` deprecation remain unchanged and are outside BUG-T12 scope.
