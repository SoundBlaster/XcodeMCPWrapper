# Active Task

- **Task ID:** FU-P6-T10-1
- **Title:** Align manual install script with Web UI configuration expectations
- **Priority:** P1
- **Phase:** Follow-up Backlog
- **Dependencies:** P6-T3, P10-T1
- **Status:** In Progress
- **Started:** 2026-02-12

## Objective
Add an explicit Web UI install mode to `scripts/install.sh` and align docs so Web UI args are only shown for environments with `.[webui]` dependencies installed.

## Next Actions
1. Add `--webui` option to install script (`pip install -e ".[webui]"`).
2. Update installation and troubleshooting docs with base vs Web UI mapping.
3. Validate behavior with/without Web UI extras and capture report.

## Recently Archived

- 2026-02-12 — P7-T12: Move Cursor IDE uvx settings before installation instructions in README (PASS)
- 2026-02-12 — FU-REBUILD-P10-T1-6: Fix uninstall.sh package detection/removal asymmetry and venv cleanup (PASS)
- 2026-02-11 — FU-REBUILD-P10-T1-5: Validate and fix documentation paths for local-running MCP server with Web UI (PASS)
