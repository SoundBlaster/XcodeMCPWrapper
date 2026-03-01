# Active Task: P2-T2

**Status:** In Progress (2026-03-01)

## Task

- **ID:** P2-T2
- **Name:** Self-healing stale socket and PID file recovery
- **Priority:** P0
- **Branch:** feature/P2-T2-stale-socket-recovery
- **Dependencies:** none

## Summary

When the broker daemon crashes or is killed, it leaves `broker.sock` and `broker.pid` on disk. The proxy's `_spawn_broker_if_needed` checks `socket_path.exists()` and skips spawning if the socket file is present — even if no process is listening. Fix by validating socket liveness via `connect()` before concluding a broker is running: if `connect()` fails with `ConnectionRefusedError`, treat both files as stale, remove them, and proceed with spawn. Also add `atexit` cleanup in the daemon so the socket file is removed on daemon exit.

## Deliverables

- `src/mcpbridge_wrapper/broker/proxy.py` — liveness check in `_spawn_broker_if_needed`
- `src/mcpbridge_wrapper/broker/daemon.py` — atexit socket cleanup on exit

## Recently Archived

- **BUG-T8** — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper (2026-03-01, PASS)
- **P1-T3** — Improve MCP settings examples in README to present broker setup first (2026-03-01, PASS)
- **P1-T2** — Add Xcode 26.4 known issue release-notes link to README (2026-02-28, PASS)
- **P1-T1** — Add the version badge in the README.md (2026-02-28, PASS)
