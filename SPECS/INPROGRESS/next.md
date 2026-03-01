# Active Task: P2-T3

**Task ID:** P2-T3
**Task Name:** Fix double-spawn race condition when MCP client toggles rapidly
**Status:** In Progress
**Branch:** feature/P2-T3-spawn-lock
**Started:** 2026-03-01

## Description

When an MCP client (e.g. Zed) toggles the connection off/on quickly, two proxy processes start simultaneously. Both check for a running broker, find none, and both spawn a daemon. Two competing daemons fight over the socket path: one wins, the other crashes. The losing proxy's client gets no broker and shows 0 tools. Fix with a filesystem lock (`fcntl.flock` on a lock file derived from the PID file path) so only one spawn attempt proceeds at a time; the second waiter re-checks liveness after acquiring the lock and connects if the first spawner succeeded.

## Recently Archived

- **P2-T1** — Replace --broker-spawn/--broker-connect with single --broker flag (2026-03-01, PASS)
- **P2-T2** — Self-healing stale socket and PID file recovery (2026-03-01, PASS)
- **BUG-T8** — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper (2026-03-01, PASS)
- **P1-T3** — Improve MCP settings examples in README to present broker setup first (2026-03-01, PASS)
- **P1-T2** — Add Xcode 26.4 known issue release-notes link to README (2026-02-28, PASS)
