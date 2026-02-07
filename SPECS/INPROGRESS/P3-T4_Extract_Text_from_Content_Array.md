# PRD: P3-T4 - Extract Text from Content Array

**Task ID:** P3-T4  
**Task Name:** Extract Text from Content Array  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a function `extract_text_content()` that finds the first content item with `type: "text"` in a content array and extracts its `text` field. This is used to retrieve the JSON payload embedded in MCP tool responses.

## Requirements

### Functional Requirements (from PRD §3.1 FR5)

- Find first content item with `type: "text"`
- Extract the `text` field value from that item
- Return None if no text items are found

## Deliverables

### Code Changes

1. Add `extract_text_content()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Mixed content with image and text (extracts first text)
   - Single text item
   - Multiple text items (extracts first)
   - No text items (returns None)
   - Empty content array
   - Text item without text field
   - Non-dict items in content array

## Acceptance Criteria

- [ ] `extract_text_content([{"type": "image"}, {"type": "text", "text": "data"}])` returns `"data"`
- [ ] `extract_text_content([{"type": "image"}])` returns `None`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T3 [✓ DONE] - Detect Non-Compliant Responses

## Implementation Notes

The function should:
1. Iterate through the content array
2. Find the first item where `type` equals `"text"`
3. Return the `text` field from that item
4. Return None if no matching item is found
5. Handle edge cases gracefully (missing fields, non-dict items)

## Design

```python
def extract_text_content(content: list) -> Optional[str]:
    """
    Extract the text field from the first content item with type "text".

    Args:
        content: A list of content items from an MCP response.

    Returns:
        The text string if found, None otherwise.
    """
```
