# Validation Report: BUG-T13

## Task
Per-Tool Latency Statistics does not show params when `capture_params` is false.

## Implementation Summary
- Added a dashboard config fetch path in `dashboard.js` to read `/api/config` and track `metrics.capture_params` on the frontend.
- Added a table-level disabled-state hint row for Per-Tool Latency Statistics when parameter capture is disabled.
- Disabled parameter toggle buttons in that state and guarded click handling against disabled toggles.
- Updated empty-pattern messaging to distinguish between:
  - capture disabled (`metrics.capture_params: true` guidance), and
  - capture enabled but no data yet.
- Added styling for disabled toggle state and the disabled-hint row.
- Added regression assertions in `tests/unit/webui/test_server.py` covering:
  - config exposure of `metrics.capture_params`,
  - frontend config fetch and conditional disabled-state rendering logic.

## Quality Gates

### 1) `PYTHONPATH=src pytest`
- Result: PASS
- Evidence: `637 passed, 5 skipped`

### 2) `ruff check src/`
- Result: PASS
- Evidence: `All checks passed!`

### 3) `PYTHONPATH=src mypy src/`
- Result: PASS
- Evidence: `Success: no issues found in 18 source files`

### 4) `PYTHONPATH=src pytest --cov`
- Result: PASS
- Evidence:
  - `637 passed, 5 skipped`
  - `Required test coverage of 90.0% reached`
  - `Total coverage: 91.33%`

## Manual Validation Notes
- When `capture_params` is disabled, the latency table now immediately shows a clear configuration hint instead of only surfacing messaging after row interaction.
- Param toggle controls are non-interactive in disabled mode to match visible state.
- Existing expanded-row behavior for enabled mode remains covered by regression assertions.

## Verdict
PASS
