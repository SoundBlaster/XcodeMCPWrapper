# FU-BUG-T6-1 Validation Report

**Task:** Document stale-process cleanup for Web UI port collisions
**Date:** 2026-02-15
**Branch:** feature/FU-BUG-T6-1-stale-process-troubleshooting
**Verdict:** PASS

---

## Quality Gates

| Gate | Command | Result |
|------|---------|--------|
| Linting | `ruff check src/` | ✅ All checks passed |
| Tests | `pytest` | ✅ 369 passed, 5 skipped, 3 warnings |
| Coverage | `pytest --cov` | ✅ 96.2% (requirement: ≥ 90%) |
| Type checking | `mypy src/` | — (not configured) |

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC1 | Entry references the exact "port already in use" warning message from BUG-T6 | ✅ Both warning strings quoted verbatim |
| AC2 | Diagnostic commands to identify the process holding the port | ✅ `lsof -i TCP:$PORT -sTCP:LISTEN` and `ps aux | grep mcpbridge` |
| AC3 | Cleanup steps to kill the stale process | ✅ `kill <PID>` and `pkill -f mcpbridge` |
| AC4 | Notes about multiple processes and verifying the correct PID | ✅ Note included at end of section |
| AC5 | Docs-only change (no code modifications) | ✅ Only `docs/troubleshooting.md` changed |

---

## Changes Made

- `docs/troubleshooting.md`: Added new section "Web UI port N is already in use" between the `zsh: no matches found` entry and the "Uptime still shows 1h 0m 0s" entry.

The section covers:
1. Two symptom variants (bridge+webui mode and --web-ui-only mode) with exact warning text
2. Root cause explanation (stale process from crashed/restarted client)
3. `lsof` and `ps` diagnosis commands
4. `kill` and `pkill` recovery steps
5. Warning about multiple concurrent processes on different ports
