# Validation Report: BUG-T14

## Task
Rows in Per-Tool Latency Statistics fold automatically immediately after unfolding.

## Implementation Summary
- Added persistent latency-row expansion tracking in `dashboard.js` via `latencyExpandedRows` keyed by tool name.
- Preserved expanded state across periodic `updateLatencyTable()` refreshes by collecting expanded rows before table redraw and reapplying expansion state after rebuild.
- Updated latency row toggle handling to persist explicit user expand/collapse actions.
- Added regression coverage in `tests/unit/webui/test_server.py` to assert presence of latency expansion-state preservation logic in served frontend bundle.

## Quality Gates

### 1) `PYTHONPATH=src pytest`
- Result: PASS
- Evidence: `631 passed, 5 skipped`

### 2) `ruff check src/`
- Result: PASS
- Evidence: `All checks passed!`

### 3) `mypy src/`
- Result: PASS
- Evidence: `Success: no issues found in 18 source files`

### 4) `PYTHONPATH=src pytest --cov`
- Result: PASS
- Evidence:
  - `631 passed, 5 skipped`
  - `Required test coverage of 90.0% reached`
  - `Total coverage: 91.33%`

## Manual Validation Notes
- The previous latency table implementation replaced tbody HTML on each refresh and reset row open state.
- New logic reapplies expansion state for tools still present after each refresh cycle.

## Verdict
PASS
