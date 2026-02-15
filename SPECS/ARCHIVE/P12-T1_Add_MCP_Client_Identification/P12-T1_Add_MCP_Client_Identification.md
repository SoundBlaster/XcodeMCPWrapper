# PRD: P12-T1 — Add MCP Client Identification

**Status:** In Progress
**Priority:** P0
**Branch:** feature/P12-T1-mcp-client-identification
**Date:** 2026-02-15

---

## Overview

Detect the calling MCP client from the `initialize` handshake. The `clientInfo` field in the initialize request contains `{name, version}`. Capture this and tag all subsequent metrics with the client identity.

---

## Deliverables

### 1. `src/mcpbridge_wrapper/schemas.py`
- Add `MCPClientInfo` model: `name: str`, `version: str`
- Add `MCPInitializeParams` model: `clientInfo: Optional[MCPClientInfo]`
- Add `get_client_info()` method to `MCPRequest` that extracts clientInfo when `method == "initialize"`

### 2. `src/mcpbridge_wrapper/__main__.py`
- In `on_request()`, detect `method == "initialize"`, extract `clientInfo.name` and `clientInfo.version`
- Call `metrics.set_client_info(name, version)` if metrics is not None
- Default to `"unknown"` if `clientInfo` is absent

### 3. `src/mcpbridge_wrapper/webui/metrics.py` (MetricsCollector)
- Add `_client_name: str` and `_client_version: str` fields (default `"unknown"`)
- Add `set_client_info(name: str, version: str)` method (thread-safe)
- Include `client_name` and `client_version` in `get_summary()` output
- Clear client info in `reset()`

### 4. `src/mcpbridge_wrapper/webui/shared_metrics.py` (SharedMetricsStore)
- Add `client_info` table: `id`, `client_name TEXT`, `client_version TEXT`, `updated_at REAL`
- Add `set_client_info(name: str, version: str)` method (upsert row)
- Include `client_name` and `client_version` in `get_summary()` output (latest row)
- Clear client info in `reset()`
- Migration: backward-compatible (nullable columns, table created if not exists)

### 5. `src/mcpbridge_wrapper/webui/server.py`
- No changes needed: `/api/metrics` already returns `metrics.get_summary()` which will include the new fields automatically

### 6. `src/mcpbridge_wrapper/webui/static/index.html`
- Add "Active Client" KPI card with id `kpi-client` (displays `name version`)

### 7. `src/mcpbridge_wrapper/webui/static/dashboard.js`
- Update `updateKPIs()` to render `summary.client_name` and `summary.client_version` in `kpi-client`
- Format: `"{name} {version}"` or `"unknown"` if not set

### 8. Tests
- `tests/unit/webui/test_metrics.py` — test `set_client_info`, summary includes fields, reset clears them
- `tests/unit/webui/test_shared_metrics.py` — test `set_client_info`, summary includes fields, reset clears them
- `tests/unit/test_main.py` — test initialize parsing calls `set_client_info` with correct values, missing clientInfo defaults to "unknown"

---

## Acceptance Criteria

- [x] `initialize` request `clientInfo.name` and `clientInfo.version` are captured
- [x] Metrics summary includes `client_name` and `client_version` fields
- [x] Dashboard displays "Active Client" KPI card (e.g. "Cursor 1.2.3")
- [x] Metrics reset clears client info
- [x] If `initialize` has no `clientInfo`, fields default to "unknown"
- [x] SQLite schema migration is backward-compatible (nullable column)
- [x] Tests cover initialize parsing, missing clientInfo, and metric tagging

---

## Implementation Notes

- `MCPRequest.params` is typed as `Optional[MCPParams]` which only has `name` and `arguments`
- Add `get_client_info()` on `MCPRequest` that raw-parses `params` as `MCPInitializeParams` when `method == "initialize"`
- Use `model_validate` with `strict=False` so unknown fields in the initialize params are ignored
- The `SharedMetricsStore.set_client_info` uses a simple single-row table (always upsert row id=1)
