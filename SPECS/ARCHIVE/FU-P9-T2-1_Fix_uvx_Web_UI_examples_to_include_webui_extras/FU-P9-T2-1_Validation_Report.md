# FU-P9-T2-1 Validation Report

**Task:** Fix uvx Web UI examples to include `webui` extras  
**Date:** 2026-02-13  
**Verdict:** PASS

## Changes Implemented

1. Updated uvx + Web UI examples to use `mcpbridge-wrapper[webui]` in:
   - `README.md`
   - `docs/cursor-setup.md`
   - `docs/claude-setup.md`
   - `docs/codex-setup.md`
2. Updated config templates for uvx + Web UI usage:
   - `config/cursor-mcp.json`
   - `config/zed-agent.json`
   - `config/claude-code.txt`
   - `config/codex-cli.txt`
3. Updated troubleshooting guidance in `docs/troubleshooting.md` to include:
   - uvx fix path with `mcpbridge-wrapper[webui]`
   - manual install fix path (`./scripts/install.sh --webui`)
   - fallback path to remove `--web-ui` args when dashboard is not needed

## Acceptance Criteria Check

| Criteria | Status | Evidence |
|---|---|---|
| No documented command/config combines `--web-ui` with base-only `uvx --from mcpbridge-wrapper` | PASS | Repository search returned no matches for base uvx + `--web-ui` patterns |
| All uvx Web UI examples use `mcpbridge-wrapper[webui]` | PASS | Updated docs/config files listed above now use `[webui]` in Web UI variants |
| Cursor JSON Web UI config no longer implies `ModuleNotFoundError: uvicorn` | PASS | `config/cursor-mcp.json` and `docs/cursor-setup.md` Web UI examples now install uvx Web UI extras |
| Troubleshooting includes both solutions | PASS | `docs/troubleshooting.md` now documents `[webui]` uvx path and removing `--web-ui` args |

## Quality Gates

Environment note:
- Initial `pytest` run failed during collection with `ModuleNotFoundError: mcpbridge_wrapper` because the package was not installed in the active interpreter.
- Installed dependencies with `python3 -m pip install -e '.[dev,webui]'`, then reran all gates.

Results:
- `pytest` -> **324 passed, 5 skipped**
- `ruff check src/` -> **All checks passed**
- `mypy src/` -> **Success: no issues found**
- `pytest --cov` -> **Total coverage 96.62%** (>= 90% requirement)

## Notes

- Test runs emitted existing non-blocking warnings related to WebSocket deprecations and a transient Web UI port `8080` bind warning from a test thread. These warnings did not affect pass/fail status.
