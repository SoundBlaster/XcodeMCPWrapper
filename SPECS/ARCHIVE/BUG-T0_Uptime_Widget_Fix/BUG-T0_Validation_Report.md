# BUG-T0 Validation Report

**Task:** Uptime widget on Web UI always shows 1h 0m 0s
**Date:** 2026-02-13
**Verdict:** PASS

---

## Changes Made

### `src/mcpbridge_wrapper/webui/shared_metrics.py`
1. Added `self._start_time: float = time.time()` in `__init__` to record service start time
2. Replaced `"uptime_seconds": window_seconds` with `"uptime_seconds": round(time.time() - self._start_time, 1)` in `get_summary()`

### `tests/unit/webui/test_shared_metrics.py`
1. Added `test_uptime_is_dynamic` — verifies uptime increases over time and is not hardcoded to 3600
2. Added `test_uptime_independent_of_window_seconds` — verifies uptime does not change when query window changes

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest` | 328 passed, 5 skipped |
| `ruff check src/` | All checks passed |
| New tests | 2/2 passed |
| Regressions | None |

## Acceptance Criteria

- [x] `get_summary()["uptime_seconds"]` returns a value that increases over time
- [x] Returned uptime reflects actual elapsed time since `SharedMetricsStore` initialization
- [x] Existing tests pass without regression
- [x] New tests cover the uptime calculation
- [x] `ruff check src/` passes
- [x] `pytest` passes
