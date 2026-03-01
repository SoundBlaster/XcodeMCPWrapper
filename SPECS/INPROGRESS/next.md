# No Active Task

**Status:** Idle — P2-T1 archived. Select the next task from `SPECS/Workplan.md`.

## Recently Archived

- **P2-T1** — Replace --broker-spawn/--broker-connect with single --broker flag (2026-03-01, PASS)
- **P2-T2** — Self-healing stale socket and PID file recovery (2026-03-01, PASS)
- **BUG-T8** — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper (2026-03-01, PASS)
- **P1-T3** — Improve MCP settings examples in README to present broker setup first (2026-03-01, PASS)
- **P1-T2** — Add Xcode 26.4 known issue release-notes link to README (2026-02-28, PASS)

## Suggested Next Tasks

- **P2-T3** (P1) — Fix double-spawn race condition when MCP client toggles rapidly (depends on P2-T2 ✅)
- **P2-T4** (P1) — Surface broker unavailability as JSON-RPC error instead of silent timeout
- **P2-T5** (P2) — Warn or restart daemon when --web-ui requested but running broker lacks it
