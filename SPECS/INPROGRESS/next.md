# Current Task

## Selected Task

- **Task ID:** FU-REBUILD-P10-T1-5
- **Name:** Validate and fix documentation paths for local-running MCP server with Web UI
- **Priority:** P1
- **Status:** In Progress
- **Selected:** 2026-02-11

## Description

Documentation for the "manual installation" / "local running" scenario contains incorrect or misleading paths to the `mcpbridge-wrapper` executable. When a user follows the recommended development setup (creating a `.venv` virtual environment), the package entry point is installed at `.venv/bin/mcpbridge-wrapper`, but configuration examples reference `~/bin/xcodemcpwrapper` (a shell wrapper that calls system `python3`, which may not have the package installed).

## Recently Archived

- 2026-02-11 — P10-T3: Recover main branch after accidental Web UI merge (PASS)
- 2026-02-11 — FU-REBUILD-P10-T1-4: Add Web UI Argument Examples for Client Configs (PASS)
