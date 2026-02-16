# Active Task

## FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions

- **Selected:** 2026-02-16
- **Branch:** feature/FU-P13-T8-web-ui-port-collision
- **Priority:** P0
- **Phase:** Phase 13 (Follow-up)
- **Dependencies:** P10-T1 ✅

### Description

Harden startup behavior when `--web-ui` port is already occupied (common with stale/orphan wrapper processes). Ensure collision handling is deterministic and does not silently degrade MCP client stability.

### Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/__main__.py` Web UI startup collision handling
- Optional single-instance guard (lock/PID) for Web UI mode
- Tests for occupied-port startup behavior
- Troubleshooting updates for stale-process cleanup

### Acceptance Criteria

- [ ] When requested Web UI port is occupied, wrapper behavior is explicit and deterministic (clear error or safe fallback)
- [ ] MCP stdio protocol output remains valid JSON-RPC only on stdout
- [ ] Repeated client startups no longer accumulate conflicting Web UI listeners on the same port
- [ ] Tests cover occupied-port and restart scenarios

## Recently Archived

- 2026-02-16 — FU-P13-T7: Enforce strict `structuredContent` compliance for empty-content tool results (PASS)
- 2026-02-16 — FU-P12-T2-1: Fix stacking click event listeners in `updateLatencyTable` (PASS)
- 2026-02-16 — FU-P11-T1-1: Refactor `_FakeWebUIConfig` test stub to use `MagicMock(spec=WebUIConfig)` (PASS)
- 2026-02-16 — FU-P11-T2-2: Add `limit` query param to `GET /api/sessions` (PASS)
- 2026-02-16 — FU-P11-T2-1: Push session data via WebSocket (PASS)
