# Current Task

## BUG-T0: Uptime widget on Web UI always shows 1h 0m 0s

- **Type:** Bug
- **Priority:** P2
- **Component:** Web UI Dashboard
- **Status:** In Progress
- **Selected:** 2026-02-13

### Description
The uptime widget on the Web UI dashboard always displays a fixed value of "1h 0m 0s" instead of showing the actual runtime uptime of the XcodeMCPWrapper process.

### Root Cause (Diagnosed)
`SharedMetricsStore.get_summary()` returns `window_seconds` (hardcoded 3600) as `uptime_seconds` instead of computing elapsed time since service start.

## Recently Archived

- 2026-02-13 — FU-P9-T2-1: Fix uvx Web UI examples to include `webui` extras (PASS)
- 2026-02-13 — FU-REBUILD-P10-T1-7: Include Web UI static assets in published package artifacts (PASS)
- 2026-02-13 — P9-T3: Release version 0.3.0 (Web UI Feature Release) (PASS)
- 2026-02-12 — FU-P8-T1-1: Reconcile P8-T1 URL criteria with current GitHub Pages path and resolve DocC reference warnings (PASS)
- 2026-02-12 — FU-P6-T10-1: Align manual install script with Web UI configuration expectations (PASS)
