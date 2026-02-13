# Active Task

- **Task ID:** FU-REBUILD-P10-T1-7
- **Task Name:** Include Web UI static assets in published package artifacts
- **Selected:** 2026-02-13
- **Phase:** Phase 10
- **Priority:** P1
- **Branch:** feature/FU-REBUILD-P10-T1-7-webui-static-assets
- **Review Subject:** webui-static-assets

## Description

Fix packaging so published artifacts include `src/mcpbridge_wrapper/webui/static/*` (`index.html`, `dashboard.css`, `dashboard.js`) and Web UI no longer serves the fallback "Static files not found." page when launched through `uvx`.

## Dependencies

- P10-T1 (done)
- P9-T3 (done)

## Planned Artifacts

- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-7_WebUI_Static_Assets.md`
- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-7_Validation_Report.md`
- `SPECS/INPROGRESS/REVIEW_webui-static-assets.md`
