# PRD: P3-T6 - Implement Fallback Wrapper for Invalid JSON

**Task ID:** P3-T6  
**Task Name:** Implement Fallback Wrapper for Invalid JSON  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P1

---

## Overview

Implement a function `parse_structured_content_with_fallback()` that attempts to parse text as JSON, but wraps it in a `{"text": content}` structure if parsing fails. This ensures that even non-JSON text content can be used as valid structuredContent.

## Requirements

### Functional Requirements (from PRD §3.1 FR7)

- Attempt to parse text as JSON
- On JSON decode error, wrap text in `{"text": content}` structure
- Always return a valid object suitable for structuredContent

## Deliverables

### Code Changes

1. Add `parse_structured_content_with_fallback()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Valid JSON object returns parsed object
   - Valid JSON array returns parsed array
   - JSON string primitive returns the string
   - Non-JSON text gets wrapped in `{"text": ...}`
   - Empty string gets wrapped
   - Complex non-JSON text gets wrapped

## Acceptance Criteria

- [ ] `parse_structured_content_with_fallback('{"key": "value"}')` returns `{"key": "value"}`
- [ ] `parse_structured_content_with_fallback('error message')` returns `{"text": "error message"}`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T5 [✓ DONE] - Parse Extracted Text as JSON

## Implementation Notes

The function should:
1. Try to parse the text using `parse_structured_content()`
2. If successful, return the parsed value
3. If JSONDecodeError is raised, wrap the original text in `{"text": text}`
4. This ensures structuredContent is always valid

## Design

```python
def parse_structured_content_with_fallback(text: str) -> Any:
    """
    Parse text as JSON, falling back to wrapped object on failure.

    Args:
        text: The text content to parse.

    Returns:
        The parsed JSON value if valid, or {"text": text} if parsing fails.
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
