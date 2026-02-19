# Validation Report — FU-P12-T1-5

**Task:** FU-P12-T1-5 — Cap `_clients` dict and prune `client_identities` to prevent unbounded growth  
**Date:** 2026-02-19  
**Verdict:** PASS

## Scope

- Added an in-memory client identity cap for `MetricsCollector` with oldest
  entry eviction based on `last_seen`.
- Added shared SQLite pruning for stale `client_identities` rows during
  `set_client_info` writes.
- Added unit tests for eviction ordering and stale identity pruning.

## Files Changed

- `src/mcpbridge_wrapper/webui/metrics.py`
- `src/mcpbridge_wrapper/webui/shared_metrics.py`
- `tests/unit/webui/test_metrics.py`
- `tests/unit/webui/test_shared_metrics.py`

## Required Quality Gates

- `pytest`
  - Result: **PASS** (`593 passed, 5 skipped, 2 warnings`)
- `ruff check src/`
  - Result: **PASS** (`All checks passed!`)
- `mypy src/`
  - Result: **PASS** (`Success: no issues found in 18 source files`)
- `pytest --cov`
  - Result: **PASS** (`593 passed, 5 skipped, 2 warnings`; total coverage **92.18%**, threshold 90%)

## Acceptance Criteria Status

- [x] `_clients` dict never exceeds the configured cap.
- [x] Stale `client_identities` rows are pruned on write.
- [x] Existing multi-client dashboard behavior is preserved.
- [x] `pytest` suite remains green.

## Notes

- Existing third-party deprecation warnings from `websockets` / `uvicorn` were
  observed during test runs and are unrelated to this task.
