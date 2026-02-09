# Web UI Dashboard Debugging Summary

## Date: 2026-02-10

## Overview

This document summarizes the debugging process and fixes applied to get the Web UI dashboard fully functional. The dashboard was showing "Connected" status but displayed no metrics or audit data when MCP tools were called.

---

## Issues Discovered and Fixed

### Issue 1: Request/Response Tracking Bug

**Problem:** The Web UI showed "Connected" but captured no data when MCP tools were called.

**Root Cause:** The original code only tracked responses from the bridge, but MCP tool calls have:
- **Request** (from Zed → bridge): `{"method": "tools/call", "params": {"name": "BuildProject"}, "id": 1}`
- **Response** (from bridge → Zed): `{"result": {...}, "id": 1}`

The original code extracted `tool_name` from each line independently. On the response line, `tool_name` was `None` (no `params.name`), so metrics were never recorded.

**Fix:** 
- Added `on_request` callback to `run_stdin_forwarder()` in `bridge.py`
- Requests are now tracked when they arrive via stdin (before being sent to bridge)
- Responses are matched to pending requests by `request_id`
- Store `(tool_name, start_time)` in `pending_requests` dict when request arrives
- Record metrics with correct latency when response arrives

**Files Modified:**
- `src/mcpbridge_wrapper/bridge.py` - Added `on_request` callback parameter
- `src/mcpbridge_wrapper/__main__.py` - Implemented request tracking logic

---

### Issue 2: Multi-Process Metrics Isolation

**Problem:** After fixing Issue 1, metrics worked but dashboard only showed data from one process. Zed starts multiple wrapper processes, each with isolated in-memory metrics.

**Root Cause:** 
- Zed MCP integration spawns multiple `xcodemcpwrapper` processes
- Each process had its own `MetricsCollector` instance in memory
- The Web UI server (one of the processes) only saw its own metrics
- Other processes' tool calls were invisible to the dashboard

**Process Layout:**
```
Zed Agent
├── Process 1: xcodemcpwrapper --web-ui --web-ui-port 8080 (with Web UI server)
├── Process 2: xcodemcpwrapper --web-ui --web-ui-port 8080 (just forwarding)
├── Process 3: xcodemcpwrapper --web-ui --web-ui-port 8080 (just forwarding)
└── ... more processes as needed
```

**Fix:**
- Created `SharedMetricsStore` class using SQLite for process-safe persistence
- Database location: `~/.cache/mcpbridge-wrapper/metrics.db`
- All processes write to the same SQLite database
- Web UI server reads aggregated metrics from the shared database
- SQLite provides thread-safe, process-safe storage

**Files Created:**
- `src/mcpbridge_wrapper/webui/shared_metrics.py` - New SQLite-based metrics store

**Files Modified:**
- `src/mcpbridge_wrapper/__main__.py` - Use `SharedMetricsStore` instead of `MetricsCollector`

---

### Issue 3: Timeseries Format Mismatch

**Problem:** Counters worked but charts ("Request timeline" and "Latency") showed no data.

**Root Cause:** Format mismatch between backend `get_timeseries()` and frontend Chart.js expectations:

**Backend returned (wrong):**
```json
{
  "data": [
    {"timestamp": "2026-02-09 21:55", "requests": 1, "errors": 0, "latency_ms": 100.0}
  ]
}
```

**Frontend expected:**
```json
{
  "requests": [{"t": 300, "v": 1}, {"t": 240, "v": 5}],
  "errors": [{"t": 300, "v": 0}, {"t": 240, "v": 0}],
  "latencies": [{"t": 300, "v": 100.0}, {"t": 240, "v": 289.9}]
}
```

Where:
- `t` = seconds ago (integer, 0 to window size)
- `v` = value (count for requests/errors, milliseconds for latency)
- Frontend buckets data into 5-second intervals for display

**Fix:**
- Rewrote `SharedMetricsStore.get_timeseries()` to return correct format
- Query individual request records instead of minute-buckets
- Bucket data by 5-second intervals to match frontend
- Return three separate arrays: `requests`, `errors`, `latencies`
- Convert timestamps to "seconds ago" format

**Files Modified:**
- `src/mcpbridge_wrapper/webui/shared_metrics.py` - Fixed `get_timeseries()` method

---

### Issue 4: Debug Logging Remnants

**Problem:** After fixes, metrics still not recording. Silent failure in `on_request` callback.

**Root Cause:** Removed `_debug()` function but left some `_debug()` calls in code, causing `NameError` exceptions that were silently caught and suppressed.

**Fix:**
- Removed all remaining `_debug()` calls from `__main__.py`
- Changed exception handler to `pass` instead of logging

**Files Modified:**
- `src/mcpbridge_wrapper/__main__.py` - Cleaned up debug logging

---

## Configuration Requirements

For the Web UI to work properly, Zed configuration must include the `--web-ui` flag:

```json
{
  "xcode-tools": {
    "command": "/Users/egor/bin/xcodemcpwrapper",
    "args": ["--web-ui", "--web-ui-port", "8080"],
    "env": {}
  }
}
```

**Note:** After changing configuration, existing wrapper processes must be killed and Zed must trigger new MCP calls to start fresh processes with the new flags.

---

## Testing Steps

1. **Kill existing processes:** `pkill -f "mcpbridge_wrapper"`
2. **Clear old database (optional):** `rm -f ~/.cache/mcpbridge-wrapper/metrics.db`
3. **Trigger MCP call in Zed:** Ask "What Xcode windows are open?" or "Build my project"
4. **Check dashboard:** Open http://localhost:8080
5. **Verify data:** 
   - Counters should show tool counts
   - Tables should show per-tool latency
   - Charts should display timeline data

---

## Files Changed

### New Files:
- `src/mcpbridge_wrapper/webui/shared_metrics.py` - SQLite-based shared metrics store
- `tests/unit/webui/test_shared_metrics.py` - Unit tests for SharedMetricsStore

### Modified Files:
- `src/mcpbridge_wrapper/bridge.py` - Added `on_request` callback to stdin forwarder
- `src/mcpbridge_wrapper/__main__.py` - Request tracking and SharedMetricsStore integration
- `tests/unit/test_main.py` - Updated tests for new stdin forwarder signature

---

## Current Status

✅ **COMPLETE** - Web UI dashboard is fully functional:
- Counters update in real-time
- Tool usage statistics display correctly
- Per-tool latency percentiles (p50/p95/p99) calculated
- Request timeline chart shows data points
- Latency chart shows data points
- Audit log captures all tool calls
- Multi-process support via SQLite shared storage

---

## Lessons Learned

1. **MCP Protocol Flow:** Tool calls involve request/response pairs - both must be tracked
2. **Multi-Process Architecture:** IDE MCP integrations spawn multiple processes - need shared storage
3. **API Contract:** Frontend/backend format must match exactly - document expected formats
4. **Debugging:** Silent exceptions in callbacks can hide issues - add proper logging
5. **Configuration Changes:** Require process restart to take effect
