# Active Task: P11-T1

**Task ID:** P11-T1
**Task Name:** Add Tool Call Detail Inspector (Request/Response Viewer)
**Phase:** Phase 11 — Web UI UX Improvements
**Priority:** P1
**Branch:** feature/P11-T1-tool-call-detail-inspector
**Started:** 2026-02-15

## Description

Add a clickable row expansion or slide-out panel in the audit table that displays the full JSON-RPC request and response payloads. Payloads are syntax-highlighted and collapsible. Backend stores truncated payloads in a bounded ring buffer (last 500, max 64KB each) behind an optional `capture_payload` config flag (default off for privacy). New API: `GET /api/audit/{request_id}/detail` returns `{request: {...}, response: {...}}`. Frontend: click audit row to expand inline or open side panel with pretty-printed JSON.

## Dependencies

- P10-T1 [✓ DONE]

## Acceptance Criteria

- [ ] `capture_payload: true` in config enables payload storage
- [ ] `GET /api/audit/{request_id}/detail` returns full request/response JSON
- [ ] Clicking an audit row in the dashboard expands to show payload detail
- [ ] Payloads are truncated at 64KB to bound storage
- [ ] Ring buffer retains last 500 payloads and evicts oldest
- [ ] Default behavior (flag off) is unchanged — no payload capture overhead
- [ ] Tests cover payload capture, retrieval, truncation, and ring buffer eviction

## Recently Archived

- 2026-02-15 — FU-BUG-T6-1: Document stale-process cleanup for Web UI port collisions (PASS)
- 2026-02-14 — BUG-T7: Unsupported `resources/*` methods can return non-standard error shape (PASS)
- 2026-02-14 — BUG-T6: Web UI port collisions create unstable multi-process behavior (PASS)
- 2026-02-14 — BUG-T5: Empty-content tool results can still violate strict `structuredContent` contract (PASS)
- 2026-02-14 — BUG-T3: Web UI cannot stay available when MCP bridge initialization fails (PASS)
- 2026-02-14 — BUG-T2: codex mcp add with Web UI extras fails in zsh (PASS)
- 2026-02-13 — FU-P9-T2-2: Add troubleshooting guidance for stale uvx cache/process versions (PASS)
