# PRD: P3-T5 - Parse Extracted Text as JSON

**Task ID:** P3-T5  
**Task Name:** Parse Extracted Text as JSON  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a function `parse_structured_content()` that parses the extracted text content as JSON. This is used to convert the text payload from MCP responses into a structured Python object that can be used as the `structuredContent` field.

## Requirements

### Functional Requirements (from PRD §3.1 FR6)

- Parse extracted text content as JSON
- Return dict for JSON objects
- Return string primitive for JSON strings
- Raise exception for invalid JSON (to be handled by caller with fallback)

## Deliverables

### Code Changes

1. Add `parse_structured_content()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Valid JSON object string parsing
   - Valid JSON array string parsing
   - JSON string primitive parsing
   - JSON number primitive parsing
   - JSON boolean/null primitive parsing
   - Invalid JSON raises exception
   - Empty string raises exception

## Acceptance Criteria

- [ ] `parse_structured_content('{"result": true}')` returns `{"result": True}`
- [ ] `parse_structured_content('"plain string"')` returns `"plain string"` (string primitive)
- [ ] Invalid JSON raises `json.JSONDecodeError`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T4 [✓ DONE] - Extract Text from Content Array

## Implementation Notes

The function should:
1. Accept a text string (typically from extract_text_content)
2. Parse it using json.loads()
3. Return the parsed value
4. Let json.JSONDecodeError propagate on failure (caller handles with fallback)

## Design

```python
def parse_structured_content(text: str) -> Any:
    """
    Parse extracted text content as JSON.

    Args:
        text: The text content to parse (typically from extract_text_content).

    Returns:
        The parsed JSON value (dict, list, str, int, float, bool, or None).

    Raises:
        json.JSONDecodeError: If the text is not valid JSON.
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
