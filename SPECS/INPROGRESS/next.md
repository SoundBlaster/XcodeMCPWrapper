# Active Task: FU-BUG-T6-1

**Task ID:** FU-BUG-T6-1
**Task Name:** Document stale-process cleanup for Web UI port collisions
**Priority:** P2
**Status:** In Progress
**Branch:** feature/FU-BUG-T6-1-stale-process-troubleshooting
**Selected:** 2026-02-15

## Description

Add a troubleshooting entry explaining how to identify and kill stale wrapper/uvx processes occupying the Web UI port. Include diagnostic commands (e.g., `lsof -i :<port>` or `ps aux | grep mcpbridge`) and cleanup steps.

## Dependencies

- BUG-T6 (completed)

## Outputs/Artifacts

- Updated `docs/troubleshooting.md` with stale-process cleanup section

## Acceptance Criteria

- [ ] Troubleshooting entry covers the "port already in use" warning message
- [ ] Commands for identifying and killing stale processes are included
- [ ] Relates the fix to the BUG-T6 warning text so users can cross-reference

## Recently Archived

- 2026-02-14 — BUG-T7: Unsupported `resources/*` methods can return non-standard error shape (PASS)
- 2026-02-14 — BUG-T6: Web UI port collisions create unstable multi-process behavior (PASS)
- 2026-02-14 — BUG-T5: Empty-content tool results can still violate strict `structuredContent` contract (PASS)
- 2026-02-14 — BUG-T3: Web UI cannot stay available when MCP bridge initialization fails (PASS)
- 2026-02-14 — BUG-T2: codex mcp add with Web UI extras fails in zsh (PASS)
- 2026-02-13 — FU-P9-T2-2: Add troubleshooting guidance for stale uvx cache/process versions (PASS)
- 2026-02-13 — FU-P9-T4-1: Align publish_helper output with protected main branch workflow (PASS)
