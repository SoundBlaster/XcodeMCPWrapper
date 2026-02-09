# P10-T2: Fix Web UI Timeseries Charts Showing No Data

## 1. Overview

### 1.1 Goal
Fix the Web UI dashboard's timeseries charts ("Request timeline" and "Latency") to correctly display data by aligning the backend `get_timeseries()` API response format with the frontend's expected format.

### 1.2 Problem Statement
The Web UI dashboard shows counters correctly (total requests, tool counts) but the timeseries charts are empty. The issue is a format mismatch:

**Backend returns:**
```json
{
  "data": [
    {"timestamp": "2026-02-09 21:55", "requests": 1, "errors": 0, "latency_ms": 100.0},
    {"timestamp": "2026-02-09 21:56", "requests": 5, "errors": 0, "latency_ms": 289.9}
  ]
}
```

**Frontend expects:**
```json
{
  "requests": [{"t": 300, "v": 1}, {"t": 240, "v": 5}],
  "errors": [{"t": 300, "v": 0}, {"t": 240, "v": 0}],
  "latencies": [{"t": 300, "v": 100.0}, {"t": 240, "v": 289.9}]
}
```

### 1.3 Root Cause
When migrating from in-memory `MetricsCollector` to SQLite-based `SharedMetricsStore` for multi-process support, the `get_timeseries()` method was implemented with a different return format than what the Chart.js frontend expects.

### 1.4 Success Criteria
- [ ] `/api/metrics/timeseries` returns data in format `{"requests": [...], "errors": [...], "latencies": [...]}`
- [ ] Each array contains objects with `t` (seconds ago, int) and `v` (value, number) properties
- [ ] Request timeline chart displays data points
- [ ] Latency chart displays data points
- [ ] Charts update in real-time via WebSocket
- [ ] All existing tests pass
- [ ] New tests verify timeseries format matches frontend expectations

---

## 2. Technical Analysis

### 2.1 Frontend Requirements (from `dashboard.js`)

The frontend expects timeseries data in this structure:

```javascript
{
  requests: [{t: seconds_ago, v: count}, ...],    // Request counts per time bucket
  errors: [{t: seconds_ago, v: count}, ...],      // Error counts per time bucket
  latencies: [{t: seconds_ago, v: latency_ms}, ...]  // Latency values per time bucket
}
```

**Time bucketing logic in frontend:**
- Frontend calls `bucketTimeseries(points, bucketSize)` to aggregate into 5-second buckets
- `t` values are "seconds ago" relative to current time
- Charts display labels as "Seconds ago" on x-axis

### 2.2 Backend Current Implementation

**File:** `src/mcpbridge_wrapper/webui/shared_metrics.py`

Current `get_timeseries()` method:
- Queries SQLite for data grouped by minute (`strftime('%Y-%m-%d %H:%M', ...)`)
- Returns `{ "data": [...] }` with string timestamps
- Does NOT separate into requests/errors/latencies arrays

### 2.3 Required Changes

1. Change time bucketing from minutes to ~5 seconds (to match frontend bucketing)
2. Return three separate arrays: `requests`, `errors`, `latencies`
3. Convert timestamps to "seconds ago" format (integers)
4. Maintain backward compatibility with existing API

---

## 3. Implementation Plan

### 3.1 Update `SharedMetricsStore.get_timeseries()`

**File:** `src/mcpbridge_wrapper/webui/shared_metrics.py`

**Changes:**
1. Query individual request records instead of minute-buckets
2. Bucket by 5-second intervals
3. Return format: `{"requests": [...], "errors": [...], "latencies": [...]}`

**Algorithm:**
```python
def get_timeseries(self, seconds: int = 300) -> Dict[str, List[Dict[str, Any]]]:
    cutoff = time.time() - seconds
    now = time.time()
    bucket_size = 5  # 5-second buckets to match frontend
    
    # Query all records in time window
    # Bucket them by (now - timestamp) // bucket_size
    # Return as {requests: [{t, v}, ...], errors: [...], latencies: [...]}
```

### 3.2 Create/Update Tests

**File:** `tests/unit/webui/test_shared_metrics.py`

Add tests:
1. `test_get_timeseries_format()` - Verify return format has requests/errors/latencies keys
2. `test_get_timeseries_t_values()` - Verify `t` values are seconds ago (integers)
3. `test_get_timeseries_v_values()` - Verify `v` values are correct counts/latencies

### 3.3 Validation

1. Run existing tests: `pytest tests/unit/webui/ -v`
2. Start Web UI: `make webui`
3. Trigger MCP calls: Use Zed to call `XcodeListWindows`, `BuildProject`, etc.
4. Verify charts: Check that Request timeline and Latency charts show data

---

## 4. Acceptance Criteria

| # | Criteria | How to Verify |
|---|----------|---------------|
| 1 | `/api/metrics/timeseries` returns correct format | `curl http://localhost:8080/api/metrics/timeseries | python -m json.tool` |
| 2 | Response has `requests`, `errors`, `latencies` arrays | Check JSON structure |
| 3 | Each point has `t` (int) and `v` (number) | Check object properties |
| 4 | `t` values are seconds ago (0 to `seconds` param) | Check value range |
| 5 | Request timeline chart displays data | Visual check in browser |
| 6 | Latency chart displays data | Visual check in browser |
| 7 | Charts update in real-time | Trigger new MCP calls, watch charts |
| 8 | All existing tests pass | `pytest tests/` |
| 9 | New tests for timeseries format | `pytest tests/unit/webui/test_shared_metrics.py` |

---

## 5. Dependencies

- P10-T1: Web UI Control & Audit Dashboard (completed)
- Files to modify:
  - `src/mcpbridge_wrapper/webui/shared_metrics.py`
  - `tests/unit/webui/test_shared_metrics.py` (create if doesn't exist)

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing API consumers | Low | Medium | Format change aligns with frontend expectations; API was already broken for UI |
| Performance issues with many records | Medium | Low | Use 5-second buckets to limit data points; SQLite indexes on timestamp |
| Timezone issues with "seconds ago" | Low | Medium | Use consistent `time.time()` (UTC) throughout |

---

## 7. Notes

- The `MetricsCollector` (in-memory) class has the correct format but is not used when Web UI is enabled with multiple processes
- `SharedMetricsStore` was created for multi-process support but has the wrong format
- This fix makes `SharedMetricsStore.get_timeseries()` match what `MetricsCollector.get_timeseries()` would return
