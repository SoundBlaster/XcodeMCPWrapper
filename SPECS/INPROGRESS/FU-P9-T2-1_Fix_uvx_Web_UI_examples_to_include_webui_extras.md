# FU-P9-T2-1 — Fix uvx Web UI examples to include `webui` extras

**Priority:** P1  
**Dependencies:** P9-T2  
**Phase:** Phase 9 Follow-up Backlog

## Objective
Remove documentation/config mismatches where users can copy a uvx command with `--web-ui` but without Web UI extras, causing runtime dependency failures.

## Deliverables
1. Update all uvx + Web UI examples to use:
   - `uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper`
2. Align client docs and config templates:
   - `README.md`
   - `docs/cursor-setup.md`
   - `docs/claude-setup.md`
   - `docs/codex-setup.md`
   - `config/cursor-mcp.json`
   - `config/zed-agent.json`
   - `config/claude-code.txt`
   - `config/codex-cli.txt`
3. Update troubleshooting guidance to include both supported paths:
   - use `[webui]` extras for uvx + `--web-ui`
   - remove `--web-ui` arguments when dashboard is not needed
4. Produce validation evidence in `SPECS/INPROGRESS/FU-P9-T2-1_Validation_Report.md`.

## Acceptance Criteria
1. No documented command/config combines `--web-ui` with base-only `uvx --from mcpbridge-wrapper`.
2. All uvx Web UI examples consistently use `mcpbridge-wrapper[webui]`.
3. Copy/paste Cursor JSON Web UI config no longer implies a `ModuleNotFoundError: uvicorn` failure.
4. Troubleshooting docs include both fix options: add `[webui]` extras or remove `--web-ui`.

## Execution Plan
1. Scan repository for `--web-ui` examples and uvx command variants.
2. Patch affected documentation and config templates only where Web UI is enabled.
3. Verify no remaining mismatched examples with targeted search checks.
4. Run quality gates:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov` (>= 90%)
5. Write and commit validation report.
