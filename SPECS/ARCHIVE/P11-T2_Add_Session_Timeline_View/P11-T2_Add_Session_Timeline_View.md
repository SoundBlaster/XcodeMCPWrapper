# PRD: P11-T2 — Add Session Timeline View

## Overview

Add a vertical session timeline view to the web dashboard that groups tool calls into sessions by idle gap. Sessions are detected using a configurable idle gap (default 300s). A new `GET /api/sessions` API returns session summaries with tool call details. The frontend adds a new "Sessions" tab with a vertical CSS timeline.

## Deliverables

### Backend

1. **`src/mcpbridge_wrapper/webui/sessions.py`** — New module:
   - `detect_sessions(entries, gap_seconds)` — Pure function that takes sorted audit entries and groups them into sessions. Returns list of session dicts.
   - Session dict schema:
     ```json
     {
       "id": "session_<index>",
       "start": 1234567890.0,
       "end": 1234567890.0,
       "tool_count": 3,
       "error_count": 1,
       "tools": [
         {
           "request_id": "abc",
           "tool": "tool_name",
           "timestamp": 1234567890.0,
           "timestamp_iso": "2026-02-15T00:00:00Z",
           "latency_ms": 42.5,
           "error": null
         }
       ]
     }
     ```

2. **`src/mcpbridge_wrapper/webui/server.py`** — Add `GET /api/sessions` endpoint:
   - Query param: `gap_seconds` (int, default from config, range 10–86400)
   - Returns `{"sessions": [...], "total": N}`

3. **`src/mcpbridge_wrapper/webui/config.py`** — Add `session_gap_seconds` setting:
   - Default value: `300`
   - New property `session_gap_seconds` on `WebUIConfig`
   - Add to `_DEFAULTS` under `"sessions"` key

### Frontend

4. **`src/mcpbridge_wrapper/webui/static/index.html`** — Add "Sessions" tab in nav, timeline markup section

5. **`src/mcpbridge_wrapper/webui/static/dashboard.js`** — Add:
   - `loadSessions()` function that fetches `/api/sessions`
   - `renderTimeline(sessions)` function
   - Tab switching to "Sessions" view
   - Real-time updates via existing WebSocket (or periodic poll)

6. **`src/mcpbridge_wrapper/webui/static/dashboard.css`** — Add timeline CSS:
   - Vertical timeline line
   - Tool call nodes with colored dots (error = red, ok = green)
   - Session header separators
   - Hover tooltip styles

### Tests

7. **`tests/unit/webui/test_sessions.py`** — Tests covering:
   - Basic session detection
   - Single-call session
   - Zero-gap edge case (each call is own session)
   - Large gap splits sessions
   - Empty entries list
   - Sessions sorted chronologically

## Acceptance Criteria

- [ ] `detect_sessions()` groups entries with gap < `gap_seconds` into same session
- [ ] `detect_sessions()` creates new session when gap >= `gap_seconds`
- [ ] Each session has `id`, `start`, `end`, `tool_count`, `error_count`, `tools` array
- [ ] `GET /api/sessions` returns `{"sessions": [...], "total": N}`
- [ ] `gap_seconds` query param accepted, validated (10–86400), defaults to config value
- [ ] `WebUIConfig.session_gap_seconds` property returns 300 by default
- [ ] Dashboard shows "Sessions" tab
- [ ] Timeline renders session groups with tool call nodes
- [ ] Tool call nodes show icon, tool name, latency, error badge
- [ ] Tests cover boundary detection, edge cases
- [ ] All tests pass, coverage ≥ 90%, ruff/mypy clean

## Dependencies

- P11-T1 (audit entries with `request_id`) ✅

## Technical Notes

- `detect_sessions()` is a pure function (no side effects, easy to test)
- Sessions are computed on-demand from in-memory audit entries (no storage overhead)
- Timeline uses pure CSS (no new JS libraries)
- Frontend click on tool call node calls existing `openDetail(request_id)` from P11-T1
