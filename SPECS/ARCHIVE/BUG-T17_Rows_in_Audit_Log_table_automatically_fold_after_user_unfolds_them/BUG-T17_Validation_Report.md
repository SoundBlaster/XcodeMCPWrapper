# Validation Report: BUG-T17

## Task
Rows in Audit Log table automatically fold after user unfolds them.

## Implementation Summary
- Added persistent audit row expansion tracking in `dashboard.js` via `auditExpandedRows` keyed by stable row identity.
- Preserved expanded state across periodic `loadAuditLogs()` refreshes by collecting and reapplying expanded rows after table redraw.
- Reset expansion state on explicit pagination/filter changes to avoid stale carry-over across different result sets.
- Added regression coverage in `tests/unit/webui/test_server.py` to assert presence of expansion-state preservation logic in served frontend bundle.

## Quality Gates

### 1) `PYTHONPATH=src pytest`
- Result: PASS
- Evidence: `630 passed, 5 skipped`

### 2) `ruff check src/`
- Result: PASS
- Evidence: `All checks passed!`

### 3) `PYTHONPATH=src mypy src/`
- Result: PASS
- Evidence: `Success: no issues found in 18 source files`

### 4) `PYTHONPATH=src pytest --cov`
- Result: PASS
- Evidence:
  - `630 passed, 5 skipped`
  - `Required test coverage of 90.0% reached`
  - `Total coverage: 91.33%`

## Manual Validation Notes
- Code path confirms previous behavior rebuilt the audit table every 5 seconds and dropped expanded row DOM state.
- New logic explicitly restores expanded state for rows still present after refresh.

## Verdict
PASS
