# Active Task: FU-P11-T2-1

**Task:** Push session data via WebSocket for real-time timeline updates
**Phase:** Phase 11 — Dashboard Enhancements
**Priority:** P3
**Branch:** `feature/FU-P11-T2-1-session-websocket-push`
**Started:** 2026-02-16
**Dependencies:** P11-T2 ✅

## Description

Extend the WebSocket `metrics_update` message in `server.py` to include current session data from `detect_sessions()`. Update `dashboard.js` to refresh the timeline on every WebSocket message instead of using the 15s poll. This fulfills the original P11-T2 acceptance criterion of "real-time via WebSocket."

## Deliverables

- Updated `src/mcpbridge_wrapper/webui/server.py` — include `sessions` key in WebSocket `metrics_update` payload
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` — consume sessions from WS message, remove 15s poll
- Tests for the new WebSocket session data
- Validation report at `SPECS/INPROGRESS/FU-P11-T2-1_Validation_Report.md`

## Acceptance Criteria

- [ ] WebSocket `metrics_update` message includes `sessions` key
- [ ] Dashboard timeline updates immediately on each WebSocket push
- [ ] 15s poll fallback removed or made redundant

## Recently Archived

- 2026-02-16 — P12-T2: Add Tool Parameter Frequency Analysis (PASS)
- 2026-02-15 — P11-T4: Add Keyboard Shortcuts & Command Palette (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (PASS)
