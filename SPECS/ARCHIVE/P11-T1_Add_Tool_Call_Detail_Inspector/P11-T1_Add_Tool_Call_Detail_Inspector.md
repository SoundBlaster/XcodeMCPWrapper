# P11-T1: Add Tool Call Detail Inspector (Request/Response Viewer)

**Phase:** Phase 11 — Web UI UX Improvements
**Priority:** P1
**Branch:** feature/P11-T1-tool-call-detail-inspector
**Date:** 2026-02-15

---

## Overview

Add a clickable row expansion panel in the audit table that displays the full JSON-RPC request and response payloads. Payloads are stored in an in-memory ring buffer (last 500 entries, max 64KB each) behind an optional `capture_payload` config flag (default off). A new API endpoint exposes payloads per `request_id`. The frontend expands an audit row inline to show pretty-printed JSON.

---

## Deliverables

1. **`src/mcpbridge_wrapper/webui/config.py`** — Add `capture_payload` flag under `audit` section (default `False`); add `audit_capture_payload` property.
2. **`src/mcpbridge_wrapper/webui/audit.py`** — Add in-memory payload ring buffer with truncation at 64KB and eviction at 500 entries; store payloads on `log()` when `capture_payload=True`; expose `get_payload(request_id)` method; accept `capture_payload` constructor arg.
3. **`src/mcpbridge_wrapper/webui/server.py`** — Add `GET /api/audit/{request_id}/detail` endpoint that returns `{request_id, request, response}` or 404 if not found or capture disabled.
4. **`src/mcpbridge_wrapper/webui/static/dashboard.js`** — Make audit rows clickable; toggle inline detail panel showing pretty-printed JSON.
5. **`src/mcpbridge_wrapper/webui/static/dashboard.css`** — Style the detail panel (monospace, scrollable, collapsible).
6. **`tests/unit/webui/test_audit.py`** — Tests for payload capture, retrieval, truncation (>64KB), ring buffer eviction (>500), and flag-off behavior.
7. **`tests/unit/webui/test_server.py`** — Tests for `GET /api/audit/{request_id}/detail` endpoint: 200 with payload, 404 on missing ID, 404 when capture disabled.

---

## Acceptance Criteria

- [ ] `capture_payload: true` in config enables payload storage
- [ ] `GET /api/audit/{request_id}/detail` returns full request/response JSON
- [ ] Clicking an audit row in the dashboard expands to show payload detail
- [ ] Payloads are truncated at 64KB to bound storage
- [ ] Ring buffer retains last 500 payloads and evicts oldest
- [ ] Default behavior (flag off) is unchanged — no payload capture overhead
- [ ] Tests cover payload capture, retrieval, truncation, and ring buffer eviction

---

## Design Notes

- **Storage:** In-memory `collections.OrderedDict` keyed by `request_id`, maintaining insertion order for FIFO eviction. Cap at 500 entries.
- **Truncation:** Both `request_data` and `response_data` are JSON-serialised then truncated to 64 * 1024 bytes before storage.
- **No SQLite:** Existing codebase uses in-memory + JSONL file storage; payload ring buffer follows the same pattern.
- **API 404:** When `capture_payload=False` or `request_id` not found, return HTTP 404 with `{"detail": "Payload not found"}`.
- **Frontend:** Click handler on audit table rows; clicking a row already expanded collapses it. Detail panel inserted as `<tr class="detail-row">` below the clicked row.

---

## Dependencies

- P10-T1 [✓ DONE] — Audit table UI must be present (it is).

---

## Risks

- No risks identified; changes are additive and isolated behind a feature flag.
