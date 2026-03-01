# Active Task: P2-T1

**Task ID:** P2-T1
**Task Name:** Replace --broker-spawn/--broker-connect with single --broker flag
**Status:** In Progress
**Branch:** feature/P2-T1-broker-flag
**Started:** 2026-03-01

## Description

Users currently must choose between `--broker-spawn` (auto-start daemon if absent) and `--broker-connect` (require daemon already running). This distinction is invisible to users — they just want broker mode. Introduce a single `--broker` flag that auto-detects: connect if daemon is alive, spawn otherwise. Keep `--broker-spawn` and `--broker-connect` as hidden aliases for backwards compatibility. Update all documentation and MCP settings examples to use `--broker`.

## Recently Archived

- **P2-T2** — Self-healing stale socket and PID file recovery (2026-03-01, PASS)
- **BUG-T8** — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper (2026-03-01, PASS)
- **P1-T3** — Improve MCP settings examples in README to present broker setup first (2026-03-01, PASS)
- **P1-T2** — Add Xcode 26.4 known issue release-notes link to README (2026-02-28, PASS)
- **P1-T1** — Add the version badge in the README.md (2026-02-28, PASS)
