# Active Task

## P13-T3: Implement multi-client transport and JSON-RPC multiplexing

- **Phase:** 13 — Persistent Broker & Shared Xcode Session
- **Priority:** P0
- **Branch:** `feature/P13-T3-multi-client-transport`
- **Selected:** 2026-02-17
- **Depends on:** P13-T2 ✅

## Description

Add local transport server (Unix socket) that accepts multiple clients and multiplexes JSON-RPC traffic to/from the single upstream bridge while preserving per-client response routing.

## Outputs/Artifacts

- `src/mcpbridge_wrapper/broker/transport.py`
- Client session manager and request ID routing map
- Backpressure/queue limits and timeout handling

## Acceptance Criteria

- [ ] At least two concurrent clients can perform tool calls successfully
- [ ] Responses are routed back to the correct client/request
- [ ] Broker handles malformed client payloads without affecting other clients
- [ ] Queue/timeout behavior is tested and deterministic

## Recently Archived

- 2026-02-17 — P13-T2: Implement persistent broker daemon with single upstream Xcode bridge (PASS)
- 2026-02-16 — P13-T1: Design persistent broker architecture and protocol contract (PASS)
- 2026-02-16 — FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions (PASS)
- 2026-02-16 — FU-P13-T7: Enforce strict `structuredContent` compliance for empty-content tool results (PASS)
- 2026-02-16 — FU-P12-T2-1: Fix stacking click event listeners in `updateLatencyTable` (PASS)
