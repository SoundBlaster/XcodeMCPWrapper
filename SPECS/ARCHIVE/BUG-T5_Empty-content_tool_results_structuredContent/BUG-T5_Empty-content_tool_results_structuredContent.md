# PRD: BUG-T5 — Empty-content tool results can still violate strict `structuredContent` contract

**Task ID:** BUG-T5
**Type:** Bug / MCP Protocol Compliance
**Priority:** P0
**Component:** Response transformation engine (`src/mcpbridge_wrapper/transform.py`)
**Date:** 2026-02-14

---

## 1. Objective Summary

`needs_transformation()` intentionally returns `False` when `result.content` is an empty list (`[]`). This means responses like `{"result": {"content": [], ...}}` are passed through without injecting `structuredContent`. Strict MCP clients that enforce the `structuredContent` field for all tool results — including those with empty content — will reject these responses.

The fix must inject `structuredContent: {}` (an empty object) when `content` is an empty array and `structuredContent` is absent, satisfying strict client expectations without breaking any existing behavior.

---

## 2. Root Cause

In `transform.py`, `needs_transformation()` short-circuits on empty content:

```python
content = result.get("content")
if isinstance(content, list) and len(content) == 0:
    return False  # BUG: skips injection for empty-content responses
```

This causes empty-content tool results to lack `structuredContent`, violating strict clients.

---

## 3. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC1 | `needs_transformation({"result": {"content": []}})` returns `True` |
| AC2 | `inject_structured_content` injects `structuredContent: {}` for empty `content` |
| AC3 | `process_response_line` outputs `structuredContent: {}` for empty-content tool results |
| AC4 | Responses already having `structuredContent` are not modified (existing behavior preserved) |
| AC5 | Non-empty content responses still get `structuredContent` injected from text (existing behavior preserved) |
| AC6 | All existing tests continue to pass |
| AC7 | `pytest` passes; `ruff check src/` clean; coverage ≥ 90% |

---

## 4. Test-First Plan

Write tests **before** modifying implementation:

### 4.1 `TestNeedsTransformation` updates
- Remove/update `test_with_empty_content_array` — it currently asserts `False`, must change to `True`
- Add `test_with_empty_content_array_already_has_structured_content` — empty content + structuredContent present → `False`

### 4.2 `TestInjectStructuredContent` updates
- Update `test_empty_content_array` — currently asserts `structuredContent` NOT injected; must now assert `structuredContent == {}`

### 4.3 `TestProcessResponseLine` additions
- Add `test_empty_content_gets_empty_structured_content` — line with `content: []` → output has `structuredContent: {}`
- Add `test_empty_content_with_existing_structured_content_unchanged` — not re-injected

---

## 5. Hierarchical TODO Plan

### Phase A: Update tests (test-first)
1. Edit `tests/unit/test_transform.py`:
   - `TestNeedsTransformation.test_with_empty_content_array`: change assertion to `True`
   - Add `test_with_empty_content_array_and_existing_structured_content`: `{"result": {"content": [], "structuredContent": {}}}` → `False`
   - `TestInjectStructuredContent.test_empty_content_array`: change assertion to `structuredContent == {}`
   - Add `TestProcessResponseLine.test_empty_content_array_gets_empty_structured_content`
   - Add `TestProcessResponseLine.test_empty_content_with_existing_structured_content`
2. Run `pytest tests/unit/test_transform.py` → expect failures on new/modified assertions

### Phase B: Fix implementation
1. Edit `src/mcpbridge_wrapper/transform.py`:
   - In `needs_transformation()`: remove the early-return guard for empty content arrays
   - In `inject_structured_content()`: when `content` is `[]` or no text item found but content exists as list, inject `structuredContent: {}`

### Phase C: Validate
1. Run `pytest tests/unit/test_transform.py` → all pass
2. Run `pytest` (full suite) → all pass
3. Run `ruff check src/` → clean
4. Run `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` → ≥ 90%
5. Create `SPECS/INPROGRESS/BUG-T5_Validation_Report.md`

---

## 6. Implementation Details

### `needs_transformation()` change

Remove this guard:
```python
if isinstance(content, list) and len(content) == 0:
    return False
```

After removal, any `result` dict with `content` key and no `structuredContent` key will trigger transformation — including empty arrays.

### `inject_structured_content()` change

Current code returns early if `extract_text_content(content)` is `None` (no text item found), leaving `structuredContent` absent. For empty content arrays or content with no `text` item, inject `{}` as fallback:

```python
text = extract_text_content(content)
if text is None:
    result["structuredContent"] = {}  # inject empty object for empty/non-text content
    return

structured = parse_structured_content_with_fallback(text)
result["structuredContent"] = structured
```

---

## 7. Notes — Docs to Update After Completion

- `SPECS/Workplan.md`: Mark BUG-T5 as ✅
- No user-facing docs require updates (internal protocol compliance fix)
- Confirm `CHANGELOG.md` or release notes if present
