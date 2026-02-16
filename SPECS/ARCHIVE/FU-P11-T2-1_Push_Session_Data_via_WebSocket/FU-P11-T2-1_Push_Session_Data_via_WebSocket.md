# PRD: FU-P11-T2-1 — Push Session Data via WebSocket for Real-Time Timeline Updates

**Task ID:** FU-P11-T2-1
**Phase:** Phase 11 — Dashboard Enhancements
**Priority:** P3
**Date:** 2026-02-16
**Branch:** `feature/FU-P11-T2-1-session-websocket-push`
**Dependencies:** P11-T2 ✅

---

## Background

P11-T2 added the session timeline view to the dashboard with a `GET /api/sessions` endpoint and a `renderTimeline()` frontend function. The original acceptance criteria included "real-time via WebSocket," but the implementation used a 15-second `setInterval` poll instead. This task completes that acceptance criterion by pushing session data through the existing WebSocket `metrics_update` message.

---

## Problem Statement

The session timeline currently refreshes on a 15-second interval (`setInterval(loadSessions, 15000)`). This is inconsistent with the rest of the dashboard (KPIs, charts, latency table) that update in real-time via WebSocket push. Users see stale session data for up to 15 seconds after a new tool call.

---

## Solution

1. **Backend (`server.py`)**: Include `sessions` in the WebSocket `metrics_update` payload by calling `detect_sessions()` on each broadcast.
2. **Frontend (`dashboard.js`)**: In `handleMetricsUpdate`, if `data.sessions` is present, call `renderTimeline(data.sessions)`. Remove the `setInterval(loadSessions, 15000)` poll. Optionally, include sessions in the HTTP fallback `startPolling()` for when WebSocket is disconnected.

---

## Deliverables

### Backend: `src/mcpbridge_wrapper/webui/server.py`

In `ws_metrics`, extend the sent JSON:

```python
# Before (current)
await websocket.send_json({
    "type": "metrics_update",
    "summary": summary,
    "timeseries": timeseries,
})

# After
entries = audit.get_entries(limit=10000)
sessions = detect_sessions(entries, gap_seconds=float(config.session_gap_seconds))
await websocket.send_json({
    "type": "metrics_update",
    "summary": summary,
    "timeseries": timeseries,
    "sessions": sessions,
})
```

The `ws_metrics` handler already has access to `audit` and `config` through closure. `detect_sessions` is already imported at the top of `server.py`.

### Frontend: `src/mcpbridge_wrapper/webui/static/dashboard.js`

1. **`handleMetricsUpdate`**: Add `renderTimeline(data.sessions)` when `data.sessions` is present:
   ```js
   function handleMetricsUpdate(data) {
       updateKPIs(data.summary);
       updateToolCharts(data.summary.tool_counts);
       updateErrorBreakdownChart(data.summary.error_counts_by_code || {});
       updateLatencyTable(data.summary.tool_latency);
       updateTimeline(data.timeseries);
       updateLatencyChart(data.timeseries);
       if (data.sessions !== undefined) {
           renderTimeline(data.sessions);
       }
   }
   ```

2. **Remove 15s poll**: Remove `setInterval(loadSessions, 15000)` from `init()`.

3. **Fallback polling**: In `startPolling()`, add sessions to the HTTP fallback (only fires when WS is closed). Include `GET /api/sessions` in the polling Promise.all and call `renderTimeline()` from the result.

### Tests: `tests/unit/webui/test_server.py`

Add a test asserting that the WebSocket `metrics_update` message includes a `sessions` key.

---

## Acceptance Criteria

- [ ] WebSocket `metrics_update` message includes `sessions` key (list of session objects)
- [ ] `handleMetricsUpdate` calls `renderTimeline(data.sessions)` when sessions are present
- [ ] `setInterval(loadSessions, 15000)` removed from `init()`
- [ ] HTTP fallback polling includes sessions (for WS-disconnected scenario)
- [ ] New test: WS message contains `sessions` key
- [ ] All existing tests pass; coverage ≥ 90%

---

## Non-Goals

- No changes to the session detection algorithm (`sessions.py`)
- No changes to the `GET /api/sessions` endpoint (kept for manual refresh button)
- No UI/CSS changes
