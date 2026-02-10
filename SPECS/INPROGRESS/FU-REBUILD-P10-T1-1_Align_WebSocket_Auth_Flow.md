# FU-REBUILD-P10-T1-1: Align WebSocket Auth Flow

## Summary
Align dashboard websocket authentication so authenticated users can reliably receive realtime updates.

## Problem
`/ws/metrics` required a `token` query parameter in auth mode while the dashboard client opened websocket connections without token propagation.

## Scope
- Update backend websocket auth to support standard `Authorization` header and token fallback.
- Inject a websocket token into dashboard HTML for client-side query-token usage.
- Update dashboard client websocket URL construction.
- Add tests for websocket auth success/failure paths.

## Deliverables
- `src/mcpbridge_wrapper/webui/server.py`
- `src/mcpbridge_wrapper/webui/static/index.html`
- `src/mcpbridge_wrapper/webui/static/dashboard.js`
- `tests/unit/webui/test_server.py`
- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-1_Validation_Report.md`

## Acceptance Criteria
- Authenticated dashboard can connect to `/ws/metrics` and receive `metrics_update` payloads.
- Websocket auth accepts valid Basic header credentials.
- Websocket auth keeps backward compatibility with `?token=` query parameter.
- Missing/invalid websocket credentials are rejected in auth mode.
- Existing server tests remain green.
