# Active Task

## P11-T2: Add Session Timeline View

- **Selected:** 2026-02-15
- **Priority:** P1
- **Dependencies:** P11-T1 ✅
- **Branch:** feature/P11-T2-session-timeline-view
- **Status:** IN PROGRESS

## Description

Add a vertical timeline view that groups tool calls into sessions detected by configurable idle gaps (default 5 min). Each session shows a compact sequence of tool calls with icons, durations, and error badges. New API: `GET /api/sessions` returns `[{id, start, end, tool_count, error_count, tools: [...]}]`. Frontend: new tab/view with vertical timeline using CSS. Each node is a tool call; hover shows summary; click opens detail inspector (P11-T1).

## Outputs/Artifacts

- New module `src/mcpbridge_wrapper/webui/sessions.py` - session detection logic
- New API endpoint `GET /api/sessions` in `src/mcpbridge_wrapper/webui/server.py`
- Updated `src/mcpbridge_wrapper/webui/static/index.html` - timeline tab
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` - timeline rendering
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.css` - timeline styling
- Updated `src/mcpbridge_wrapper/webui/config.py` - `session_gap_seconds` setting
- Tests in `tests/unit/webui/test_sessions.py`

## Acceptance Criteria

- [ ] Sessions are detected by idle gap (configurable, default 300s)
- [ ] `GET /api/sessions` returns session list with tool call summaries
- [ ] Dashboard displays vertical timeline with tool call nodes
- [ ] Hover on node shows tool name, latency, error status
- [ ] Click on node opens detail inspector (if P11-T1 payload capture enabled)
- [ ] Sessions update in real-time via existing WebSocket stream
- [ ] Tests cover session boundary detection, edge cases (single-call sessions, zero-gap)

## Recently Archived

- 2026-02-15 — BUG-T8: Audit log cross-process visibility (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (Request/Response Viewer) (PASS)
- 2026-02-15 — FU-BUG-T6-1: Document stale-process cleanup for Web UI port collisions (PASS)
- 2026-02-14 — BUG-T7: Unsupported `resources/*` methods can return non-standard error shape (PASS)
- 2026-02-14 — BUG-T6: Web UI port collisions create unstable multi-process behavior (PASS)
