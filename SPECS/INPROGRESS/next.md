# Active Task: P13-T4

## Selected Task

**ID:** P13-T4
**Name:** Add stdio proxy mode for compatibility with existing MCP clients
**Priority:** P1
**Branch:** feature/P13-T4-stdio-proxy-mode
**Selected:** 2026-02-18

## Description

Implement a proxy mode where standard MCP clients still use stdio, but the wrapper process forwards traffic to the persistent local broker instead of spawning a new upstream bridge.

## Dependencies

- P13-T3 ✅ (multi-client transport and JSON-RPC multiplexing — completed 2026-02-18)

## Outputs/Artifacts

- CLI flags for broker usage (`--broker-connect`, `--broker-spawn`)
- Proxy adapter module under `src/mcpbridge_wrapper/broker/proxy.py`
- Backward-compatible default behavior toggle strategy

## Acceptance Criteria

- [ ] Existing MCP client configs can opt into broker mode with minimal changes
- [ ] Proxy process exit does not terminate broker daemon
- [ ] Legacy direct mode remains available for fallback
- [ ] Unit tests cover proxy connect/disconnect and reconnect behavior

## Recently Archived

- 2026-02-18 — P13-T3: Implement multi-client transport and JSON-RPC multiplexing (PASS)
- 2026-02-17 — P13-T2: Implement persistent broker daemon with single upstream Xcode bridge (PASS)
- 2026-02-16 — P13-T1: Design persistent broker architecture and protocol contract (PASS)
- 2026-02-16 — FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions (PASS)
- 2026-02-16 — FU-P13-T7: Enforce strict `structuredContent` compliance for empty-content tool results (PASS)
