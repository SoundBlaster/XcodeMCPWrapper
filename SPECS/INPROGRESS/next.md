# Active Task

## P13-T2: Implement persistent broker daemon with single upstream Xcode bridge

- **Phase:** 13 — Persistent Broker & Shared Xcode Session
- **Priority:** P0
- **Branch:** feature/P13-T2-broker-daemon
- **Selected:** 2026-02-16
- **Dependencies:** P13-T1 ✅

### Description

Add daemon mode that launches and owns one `xcrun mcpbridge` subprocess, keeps
it alive, and exposes broker readiness state to clients.

### Outputs / Artifacts

- `src/mcpbridge_wrapper/broker/daemon.py` — full implementation replacing stub
- PID/lock handling + stale lock cleanup
- Health endpoint or status command (`broker status`)

### Acceptance Criteria

- [ ] Starting broker twice does not spawn duplicate upstream bridge instances
- [ ] Broker survives client disconnects without restarting upstream bridge
- [ ] Graceful shutdown terminates upstream process and cleans lock/socket files
- [ ] Crash recovery path is covered by tests
