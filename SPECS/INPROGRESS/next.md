# Active Task

## P12-T1: Add MCP Client Identification

- **Phase:** Phase 12 — Data Collection Enhancements
- **Priority:** P0
- **Branch:** feature/P12-T1-mcp-client-identification
- **Started:** 2026-02-15
- **Dependencies:** P10-T1 ✅

## Description

Detect the calling MCP client from the `initialize` handshake. The `clientInfo` field in the initialize request contains `{name, version}`. Capture this and tag all subsequent metrics with the client identity. Add `client` column to shared metrics SQLite schema. Dashboard: new KPI card "Active Client" showing the connected client name and version. Charts: optional client-based breakdown in tool usage.

## Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/__main__.py` - extract `clientInfo` from initialize request
- Updated `src/mcpbridge_wrapper/schemas.py` - add `MCPInitializeParams` model with `clientInfo`
- Updated `src/mcpbridge_wrapper/webui/metrics.py` - `client_name` field in metrics
- Updated `src/mcpbridge_wrapper/webui/shared_metrics.py` - `client` column in SQLite schema
- Updated `src/mcpbridge_wrapper/webui/server.py` - expose client info in metrics summary
- Updated `src/mcpbridge_wrapper/webui/static/index.html` - "Active Client" KPI card
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` - render client KPI
- Tests in `tests/unit/test_main.py` and `tests/unit/webui/test_metrics.py`

## Acceptance Criteria

- [ ] `initialize` request `clientInfo.name` and `clientInfo.version` are captured
- [ ] Metrics summary includes `client_name` and `client_version` fields
- [ ] Dashboard displays "Active Client" KPI card (e.g. "Cursor 1.2.3")
- [ ] Metrics reset clears client info
- [ ] If `initialize` has no `clientInfo`, fields default to "unknown"
- [ ] SQLite schema migration is backward-compatible (nullable column)
- [ ] Tests cover initialize parsing, missing clientInfo, and metric tagging

## Recently Archived

- 2026-02-15 — P11-T4: Add Keyboard Shortcuts & Command Palette (PASS)
- 2026-02-15 — P11-T3: Add Dashboard Theme Toggle (Dark/Light) (PASS)
- 2026-02-15 — P11-T2: Add Session Timeline View (PASS)
- 2026-02-15 — BUG-T8: Audit log cross-process visibility (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (Request/Response Viewer) (PASS)
