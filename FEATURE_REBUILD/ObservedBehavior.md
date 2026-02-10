# Observed Behavior Matrix - Web UI Feature (P10-T1/P10-T2 Baseline)

## Scope
Observed runtime behavior for the optional Web UI dashboard feature on source branch `feature/p10-t1-web-ui`.

## Behavior Matrix

| ID | Trigger | Key Inputs | Outputs | Side Effects | Evidence |
|---|---|---|---|---|---|
| B-001 | Start wrapper with `--web-ui` | CLI flags, config path, env overrides | Web server thread starts; startup URL written to stderr | Creates/open metrics DB and audit log directory | `src/mcpbridge_wrapper/__main__.py`, `src/mcpbridge_wrapper/webui/server.py` |
| B-002 | MCP request enters stdin | JSON-RPC `tools/call` with id and tool name | Request and in-flight counters increase | Shared metrics record inserted | `src/mcpbridge_wrapper/bridge.py`, `src/mcpbridge_wrapper/__main__.py`, `tests/unit/test_main.py` |
| B-003 | MCP response exits stdout | JSON-RPC response with matching id | Latency and error metrics updated; audit entry logged | Pending request map entry removed | `src/mcpbridge_wrapper/__main__.py`, `tests/unit/test_main.py` |
| B-004 | `GET /api/metrics`, `GET /api/metrics/timeseries` | Optional seconds query | Summary and chart payload returned | None | `src/mcpbridge_wrapper/webui/server.py`, `tests/unit/webui/test_server.py` |
| B-005 | `POST /api/metrics/reset` | Authenticated request | Reset confirmation JSON | Metrics storage cleared | `src/mcpbridge_wrapper/webui/server.py`, `src/mcpbridge_wrapper/webui/shared_metrics.py` |
| B-006 | `GET /api/audit*` routes | Pagination/filter/export params | Paginated entries + JSON/CSV downloads | None for reads | `src/mcpbridge_wrapper/webui/server.py`, `src/mcpbridge_wrapper/webui/audit.py` |
| B-007 | `WS /ws/metrics` connection | Optional auth token query param | Periodic `metrics_update` events | Connection tracked in server state | `src/mcpbridge_wrapper/webui/server.py` |
| B-008 | WebSocket closed/unavailable | Browser timer tick | HTTP polling keeps dashboard data fresh every 2s | None | `src/mcpbridge_wrapper/webui/static/dashboard.js` |

## Known Bugs and Gaps

| ID | Symptom | Severity | Evidence |
|---|---|---|---|
| BUG-001 | Historical timeseries format mismatch produced empty charts (fixed baseline requirement) | P1 | `SPECS/INPROGRESS/Web_UI_Debugging_Summary.md`, `SPECS/ARCHIVE/P10-T2_Fix_Web_UI_Timeseries_Charts/P10-T2_Fix_Web_UI_Timeseries_Charts.md` |
| BUG-002 | Auth-enabled dashboards can fail WebSocket auth because frontend does not pass backend-required token | P2 | `src/mcpbridge_wrapper/webui/server.py`, `src/mcpbridge_wrapper/webui/static/dashboard.js` |
| BUG-003 | Invalid `--web-ui-port` value can crash with `ValueError` | P2 | `src/mcpbridge_wrapper/__main__.py` |
| BUG-004 | Docs mention `MCP_WRAPPER_WEB_UI*` env vars that runtime does not read | P2 | `docs/webui-setup.md`, `src/mcpbridge_wrapper/__main__.py`, `src/mcpbridge_wrapper/webui/config.py` |

## Compatibility Contracts (Must Preserve)

1. No behavior change when wrapper starts without `--web-ui`.
2. Dashboard UI remains at `/` and serves bundled static assets.
3. `GET /api/metrics` response keys remain stable.
4. `GET /api/metrics/timeseries` keeps `{requests, errors, latencies}` arrays of `{t, v}`.
5. Audit API and export endpoints remain backward-compatible.
6. Shared metrics persistence remains process-safe.
