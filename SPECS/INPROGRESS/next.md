# Active Task: P12-T2

## Task Metadata

- **ID:** P12-T2
- **Name:** Add Tool Parameter Frequency Analysis
- **Priority:** P3
- **Dependencies:** P12-T1 ✅
- **Branch:** feature/P12-T2-tool-parameter-frequency-analysis
- **Selected:** 2026-02-16

## Description

Optionally capture and aggregate tool call parameter keys (not values by default) for pattern analysis. Config flag `capture_params: bool` (default off). On request capture, extract `params.arguments` key names. Store parameter key signatures per tool (e.g. `XcodeGrep(pattern, path, tabIdentifier)`). New API: `GET /api/analytics/param-patterns?tool=<name>` returns top-N parameter combinations. Dashboard: expandable section in latency table showing common param combos.

## Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/__main__.py` - extract argument keys from tool call params
- New module or section in `src/mcpbridge_wrapper/webui/metrics.py` - param pattern aggregation
- Updated `src/mcpbridge_wrapper/webui/shared_metrics.py` - `param_keys` column in requests table
- New API endpoint `GET /api/analytics/param-patterns` in `src/mcpbridge_wrapper/webui/server.py`
- Updated `src/mcpbridge_wrapper/webui/config.py` - `capture_params` flag
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` - param pattern display
- Tests in `tests/unit/webui/test_metrics.py`

## Acceptance Criteria

- [ ] `capture_params: true` enables parameter key capture
- [ ] Only argument key names are stored (not values) by default
- [ ] `GET /api/analytics/param-patterns?tool=XcodeGrep` returns ranked param combos
- [ ] Dashboard shows expandable param pattern info per tool
- [ ] Default behavior (flag off) is unchanged — no extra capture overhead
- [ ] Tests cover param extraction, aggregation, and API response format

## Recently Archived

- 2026-02-15 — P12-T4: Add documentation about data storage (PASS)
- 2026-02-15 — P12-T3: Add Error Classification & Categorization (PASS)
- 2026-02-15 — P12-T1: Add MCP Client Identification (PASS)
- 2026-02-15 — P11-T4: Add Keyboard Shortcuts & Command Palette (PASS)
- 2026-02-15 — P11-T3: Add Dashboard Theme Toggle (Dark/Light) (PASS)
