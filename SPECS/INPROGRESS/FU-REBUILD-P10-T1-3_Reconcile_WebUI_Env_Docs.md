# FU-REBUILD-P10-T1-3: Reconcile Web UI Environment Docs

## Summary
Reconcile `docs/webui-setup.md` environment-variable instructions with actual runtime support.

## Problem
The docs currently mention `MCP_WRAPPER_WEB_UI*` variables for enabling Web UI, but runtime enables Web UI only through CLI `--web-ui` and reads `WEBUI_*` for config overrides.

## Scope
- Update `docs/webui-setup.md` to remove unsupported env-enable instructions.
- Clarify that `--web-ui` is required to start dashboard.
- Keep and clarify supported `WEBUI_*` override examples.

## Deliverables
- `docs/webui-setup.md`
- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-3_Validation_Report.md`

## Acceptance Criteria
- Documentation no longer references unsupported `MCP_WRAPPER_WEB_UI*` toggles.
- Documentation explicitly states `--web-ui` is required.
- Environment variable section reflects only runtime-supported `WEBUI_*` settings.
