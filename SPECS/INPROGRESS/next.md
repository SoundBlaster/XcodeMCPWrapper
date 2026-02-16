# Active Task

## P13-T1: Design persistent broker architecture and protocol contract

- **Phase:** 13 — Persistent Broker & Shared Xcode Session
- **Priority:** P0
- **Branch:** feature/P13-T1-persistent-broker-architecture
- **Selected:** 2026-02-16

### Description

Define daemon lifecycle, client transport choice (Unix domain socket first), request/response correlation strategy, reconnect behavior, and failure boundaries between broker, upstream bridge, and client proxies.

### Dependencies

- P2-T6 (subprocess wrapper) ✅
- P3-T10 (response transformation) ✅

### Outputs/Artifacts

- Broker architecture spec (sequence diagrams and lifecycle states)
- ADR documenting transport and security choices
- Initial module scaffold under `src/mcpbridge_wrapper/broker/`

### Acceptance Criteria

- [ ] Architecture covers startup, shutdown, reconnect, and stale-socket recovery
- [ ] Correlation strategy for concurrent JSON-RPC requests is specified
- [ ] Security boundary for local clients is documented (socket permissions/token)
- [ ] Design is reviewed and approved for implementation

## Recently Archived

- 2026-02-16 — FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions (PASS)
- 2026-02-16 — FU-P13-T7: Enforce strict `structuredContent` compliance for empty-content tool results (PASS)
- 2026-02-16 — FU-P12-T2-1: Fix stacking click event listeners in `updateLatencyTable` (PASS)
- 2026-02-16 — FU-P11-T1-1: Refactor `_FakeWebUIConfig` test stub to use `MagicMock(spec=WebUIConfig)` (PASS)
- 2026-02-16 — FU-P11-T2-2: Add `limit` query param to `GET /api/sessions` (PASS)
