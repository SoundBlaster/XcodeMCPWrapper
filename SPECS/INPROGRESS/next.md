# Next Task: BUG-T9 — Fix broker daemon not sending notifications/initialized before tools/list probe

**Priority:** P0
**Phase:** Bug Fixes
**Effort:** Small
**Dependencies:** P4-T2
**Status:** In Progress

## Description

After the broker's own `initialize` probe succeeds, it immediately sends a `tools/list` probe without first sending the `notifications/initialized` notification. xcrun mcpbridge requires this notification to complete the MCP handshake before it responds to any subsequent requests, so it queues `tools/list` indefinitely. `_read_upstream_loop` blocks forever on `readline()` waiting for the tools/list response; all client requests forwarded to upstream never get responses; every client socket times out.

## Outputs/Artifacts

- `src/mcpbridge_wrapper/broker/daemon.py` — send `notifications/initialized` before `tools/list` probe
- `tests/unit/test_broker_daemon.py` — assert notification is sent before probe with correct ordering

## Recently Archived

- **P5-T1** (2026-03-06): Release 0.4.0 to PyPI and MCP Registry — PASS
- **P1-T11** (2026-03-06): Update test coverage badge in README.md with actual numbers — PASS
- **P4-T2** (2026-03-06): Cache tools/list in broker and gate client responses on upstream readiness — PASS
- **P1-T10** (2026-03-06): Document Xcode first-approval timing race — PASS
