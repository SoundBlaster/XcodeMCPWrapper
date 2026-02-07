# PRD: P3-T7 - Inject structuredContent into Result

**Task ID:** P3-T7  
**Task Name:** Inject structuredContent into Result  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a function `inject_structured_content()` that adds the `structuredContent` field to an MCP response's result object. This is the core transformation that makes non-compliant MCP responses compatible with strict MCP clients like Cursor.

## Requirements

### Functional Requirements (from PRD §3.1 FR6-FR7)

- Add `structuredContent` field to result object
- Use parsed JSON value from text content
- Apply fallback wrapper for non-JSON text
- Mutate the data structure in place

## Deliverables

### Code Changes

1. Add `inject_structured_content()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Inject structuredContent into result with valid JSON text
   - Inject structuredContent with non-JSON text (fallback wrapper)
   - Verify mutation happens in place
   - Verify content array is preserved

## Acceptance Criteria

- [ ] `inject_structured_content(data)` adds `structuredContent` to `data["result"]`
- [ ] Valid JSON text becomes parsed structuredContent
- [ ] Non-JSON text becomes `{"text": content}` structuredContent
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T5 [✓ DONE] - Parse Extracted Text as JSON
- P3-T6 [✓ DONE] - Implement Fallback Wrapper for Invalid JSON

## Implementation Notes

The function should:
1. Extract text from content array using `extract_text_content()`
2. Parse with fallback using `parse_structured_content_with_fallback()`
3. Add the result as `structuredContent` field to the result object
4. Mutate the data in place (no return value needed)

## Design

```python
def inject_structured_content(data: dict) -> None:
    """
    Inject structuredContent into an MCP response's result object.

    This function mutates the input data dictionary in place, adding
    the structuredContent field parsed from the content array's text.

    Args:
        data: The MCP response dictionary to transform. Must have a
              'result' key with a 'content' array.
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
