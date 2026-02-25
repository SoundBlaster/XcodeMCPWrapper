# Next Task: BUG-T9 — Orphaned Web UI server process blocks port after MCP client disconnect or config change

**Priority:** P1
**Phase:** Known Issues / Bug Tracker
**Effort:** 4-6 hours
**Dependencies:** None
**Status:** Selected

## Description

Prevent orphaned wrapper processes from keeping `--web-ui-port` bound after stdin disconnects, by detecting client disconnect and forcing deterministic upstream bridge shutdown with timeout-backed termination.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
