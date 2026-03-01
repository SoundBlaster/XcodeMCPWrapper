# Active Task: P1-T4

**Status:** Selected — P1-T4 in progress

## Task

- **ID:** P1-T4
- **Name:** Update docs to reflect broker robustness improvements (P2-T1 – P2-T5)
- **Branch:** feature/P1-T4-docs-broker-robustness
- **Priority:** P2
- **Dependencies:** P2-T1, P2-T2, P2-T4, P2-T5 (all completed)

## Description

Update five `docs/` markdown files and four DocC mirror files to reflect the changes shipped in Phase 2 broker robustness tasks:

- **P2-T1** — `--broker` flag replaces `--broker-spawn`/`--broker-connect` as the recommended option
- **P2-T2** — stale socket/PID recovery is now automatic for `--broker`/`--broker-spawn`
- **P2-T4** — broker unavailability surfaces as JSON-RPC -32001 error, not silent hang
- **P2-T5** — proxy warns to stderr when `--web-ui` requested but running broker lacks it

## Files to Update

- `docs/broker-mode.md`
- `docs/troubleshooting.md`
- `docs/cursor-setup.md`
- `docs/claude-setup.md`
- `docs/codex-setup.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/CursorSetup.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/ClaudeCodeSetup.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`

## Recently Archived

- **P2-T5** — Warn or restart daemon when --web-ui requested but running broker lacks it (2026-03-01, PASS)
- **P2-T4** — Surface broker unavailability as JSON-RPC error instead of silent timeout (2026-03-01, PASS)
- **P2-T3** — Fix double-spawn race condition when MCP client toggles rapidly (2026-03-01, PASS)
- **P2-T1** — Replace --broker-spawn/--broker-connect with single --broker flag (2026-03-01, PASS)
- **P2-T2** — Self-healing stale socket and PID file recovery (2026-03-01, PASS)
