# Active Task

## Selected Task

- **Task ID:** FU-P13-T7
- **Name:** Fix_structuredContent_compliance_for_empty_content_tool_results
- **Priority:** P0
- **Selected:** 2026-02-16
- **Branch:** feature/FU-P13-T7-structuredcontent-compliance

## Description

Fix transformation logic so strict MCP clients no longer fail when a tool response includes `result.content: []` without `result.structuredContent`. Add a fallback injection strategy for transformable tool results with empty content.

## Dependencies

- P3-T3 ✅
- P4-T1 ✅
- P5-T6 ✅

## Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/transform.py` transformation conditions for empty-content results
- Updated `tests/unit/test_transform.py` coverage for strict empty-content compliance
- Updated troubleshooting/docs note clarifying strict-client behavior

## Acceptance Criteria

- [ ] For tool responses missing `structuredContent`, empty `content` results are normalized to include `structuredContent` fallback
- [ ] Existing already-compliant responses remain unchanged
- [ ] Non-tool JSON-RPC notifications and unrelated payloads are not regressed
- [ ] New unit tests fail before fix and pass after fix

## Recently Archived

- 2026-02-16 — FU-P12-T2-1: Fix stacking click event listeners in `updateLatencyTable` (PASS)
- 2026-02-16 — FU-P11-T1-1: Refactor `_FakeWebUIConfig` test stub to use `MagicMock(spec=WebUIConfig)` (PASS)
- 2026-02-16 — FU-P11-T2-2: Add `limit` query param to `GET /api/sessions` (PASS)
- 2026-02-16 — FU-P11-T2-1: Push session data via WebSocket (PASS)
- 2026-02-16 — P12-T2: Add Tool Parameter Frequency Analysis (PASS)
