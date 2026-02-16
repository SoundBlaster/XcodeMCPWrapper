# PRD: FU-P13-T7 — Enforce strict `structuredContent` compliance for empty-content tool results

**Created:** 2026-02-16
**Priority:** P0
**Branch:** feature/FU-P13-T7-structuredcontent-compliance
**Status:** PLAN

---

## Problem Statement

Strict MCP clients (Cursor, Codex) validate that every `tools/call` response includes a
`structuredContent` field. When Xcode MCP bridge returns `result.content: []` without
`result.structuredContent`, these clients raise a schema violation and may abort the session.

---

## Current State

The core injection logic **is already present** (implemented in P4-T1 / BUG-T5):

- `needs_transformation()` returns `True` for `content: []` (no `structuredContent`)
- `inject_structured_content()` injects `structuredContent: {}` for empty arrays
- Basic unit tests cover this path (`test_empty_content_array_gets_empty_structured_content`)

**Gap 1 — Missing edge-case coverage:** No test covers `tools/call` with `isError=true`
and `content: []` together. In this scenario, `normalize_resources_error` skips the
response (method == `tools/call`), then `inject_structured_content` injects `{}` as
expected — but this flow has no dedicated regression test.

**Gap 2 — Missing documentation:** `troubleshooting.md` has no section explaining the
`structuredContent` compliance requirement for strict clients, so users hitting this
error have no guidance.

---

## Deliverables

| # | Artifact | Description |
|---|----------|-------------|
| 1 | `tests/unit/test_transform.py` | Add targeted tests for `isError=true` + `content:[]` on `tools/call`; add test verifying non-tool notifications are unaffected |
| 2 | `docs/troubleshooting.md` | Add section: "Tool has empty content but no structuredContent (strict MCP clients)" |

No changes to `src/mcpbridge_wrapper/transform.py` — the implementation is already
correct and complete.

---

## Acceptance Criteria

- [x] For tool responses missing `structuredContent`, empty `content` results are
      normalized to include `structuredContent` fallback *(already implemented)*
- [x] Existing already-compliant responses remain unchanged *(covered by existing tests)*
- [x] Non-tool JSON-RPC notifications and unrelated payloads are not regressed
      *(covered by existing tests)*
- [ ] New unit tests fail before fix and pass after fix — *applied as: new tests
      added to prevent future regression; they pass on current codebase which contains
      the fix*
- [ ] `docs/troubleshooting.md` section added for strict-client empty-content behavior

---

## Test Plan

### New tests in `TestProcessResponseLine`

1. `test_tools_call_iserror_true_empty_content_gets_structured_content`
   Input: `{"jsonrpc":"2.0","id":1,"result":{"isError":true,"content":[]}}`
   Method: `tools/call`
   Expected: `result.structuredContent == {}`

2. `test_non_tool_notification_no_result_unchanged`
   Input: `{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}`
   Method: `None`
   Expected: line unchanged (no result → no transformation)

3. `test_empty_content_response_roundtrip_with_other_fields`
   Verify `id`, `jsonrpc`, `isError` fields are preserved after injection.

---

## Docs Update Plan

Add a new subsection to `docs/troubleshooting.md` under **Common Errors**:

```
### "Tool has output schema but did not return structured content" (empty result)

**Symptom:** Cursor/Codex reports a schema violation even though the tool ran successfully.

**Cause:** The Xcode MCP bridge returned `result.content: []` (empty) without a
`structuredContent` field. Strict MCP clients require `structuredContent` on every
tool response.

**Solution:** mcpbridge-wrapper automatically injects `structuredContent: {}` for
empty-content tool responses. Ensure you are using mcpbridge-wrapper (not connecting
directly to `xcrun mcpbridge`).
```

---

## Dependencies

- P3-T3 ✅ (transformation engine)
- P4-T1 ✅ (empty-content skip logic / inject)
- P5-T6 ✅ (process_response_line integration)
