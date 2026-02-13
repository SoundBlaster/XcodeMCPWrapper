# BUG-T0: Uptime widget on Web UI always shows 1h 0m 0s

**Type:** Bug Fix
**Priority:** P2
**Component:** Web UI Dashboard — SharedMetricsStore
**Created:** 2026-02-13

---

## Problem Statement

The Web UI dashboard uptime widget always displays "1h 0m 0s" regardless of actual process runtime. The root cause is that `SharedMetricsStore.get_summary()` returns `window_seconds` (the query window parameter, default 3600) as `uptime_seconds`, instead of computing actual elapsed time.

## Root Cause

**File:** `src/mcpbridge_wrapper/webui/shared_metrics.py`, line 197
```python
"uptime_seconds": window_seconds,  # Approximate
```

The `MetricsCollector` (in-memory, single-process) correctly tracks uptime via `self._start_time = time.time()` and computes `now - self._start_time`. The `SharedMetricsStore` (SQLite-based, multi-process) lacks this mechanism entirely.

## Data Flow

```
dashboard.js → /api/metrics → SharedMetricsStore.get_summary()
                                  ↓
                          returns window_seconds=3600
                                  ↓
                          formatUptime(3600) → "1h 0m 0s"
```

## Deliverables

1. **Track service start time in `SharedMetricsStore`** — store `_start_time` in `__init__` (analogous to `MetricsCollector`)
2. **Return actual uptime in `get_summary()`** — compute `time.time() - self._start_time` instead of `window_seconds`
3. **Add unit tests** — verify uptime increases over time and is not a fixed value
4. **Create validation report**

## Acceptance Criteria

- [ ] `get_summary()["uptime_seconds"]` returns a value that increases over time
- [ ] The returned uptime reflects actual elapsed time since `SharedMetricsStore` initialization
- [ ] Existing tests pass without regression
- [ ] New tests cover the uptime calculation
- [ ] `ruff check src/` passes
- [ ] `pytest` passes

## Task Plan

### Task 1: Fix `SharedMetricsStore.get_summary()` uptime calculation
- Add `self._start_time = time.time()` in `__init__`
- Replace `window_seconds` with `round(time.time() - self._start_time, 1)` in `get_summary()` return dict

### Task 2: Write unit tests
- Test that `get_summary()` returns a dynamic uptime value > 0
- Test that uptime increases between successive calls
- Test that uptime does not equal `window_seconds`

### Task 3: Run quality gates
- `pytest` — all tests pass
- `ruff check src/` — no lint errors
- Coverage check on modified files

## Dependencies

- None (self-contained fix)

## Risk Assessment

- **Low risk** — single-line fix in a well-understood method with a correct reference implementation in `MetricsCollector`
