# Active Task

## Current Task

- **Task ID:** FU-REBUILD-P10-T1-6
- **Task Name:** Fix uninstall.sh package detection/removal asymmetry and venv cleanup
- **Priority:** P2
- **Status:** IN PROGRESS
- **Selected:** 2026-02-12

## Task Summary

Fix the logic mismatch in `scripts/uninstall.sh` between detection and removal of pip packages. Detection checks for both `mcpbridge-wrapper` and `xcodemcpwrapper`, but removal only targets `mcpbridge-wrapper`. Also add venv cleanup support since `install.sh` now creates a `.venv`.

## Recently Archived

- 2026-02-11 — FU-REBUILD-P10-T1-5: Validate and fix documentation paths for local-running MCP server with Web UI (PASS)
- 2026-02-11 — P10-T3: Recover main branch after accidental Web UI merge (PASS)
- 2026-02-11 — FU-REBUILD-P10-T1-4: Add Web UI Argument Examples for Client Configs (PASS)
