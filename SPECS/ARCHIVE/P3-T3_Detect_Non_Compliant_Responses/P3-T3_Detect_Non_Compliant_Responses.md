# PRD: P3-T3 - Detect Non-Compliant Responses

**Task ID:** P3-T3  
**Task Name:** Detect Non-Compliant Responses  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a function `needs_transformation()` that identifies MCP responses that have a `content` field but are missing the required `structuredContent` field. This is the core detection logic for the MCP compliance fix.

## Requirements

### Functional Requirements (from PRD §3.1 FR4)

- Detect responses with `content` field but missing `structuredContent`
- Return True for non-compliant responses that need transformation
- Return False for already compliant responses (have `structuredContent`)

## Deliverables

### Code Changes

1. Add `needs_transformation()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Response with content but no structuredContent (needs transformation)
   - Response with structuredContent present (no transformation needed)
   - Response without result field
   - Response with empty content array
   - Response with content but null result

## Acceptance Criteria

- [ ] `needs_transformation({"result": {"content": []}})` returns `True`
- [ ] `needs_transformation({"result": {"content": [], "structuredContent": {}}})` returns `False`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T2 [✓ DONE] - Implement JSON Parsing with Error Handling

## Implementation Notes

The function should:
1. Check if the input is a dictionary with a 'result' key
2. Check if 'result' is a dictionary with 'content' key
3. Check if 'structuredContent' is NOT present in 'result'
4. Return True only if all conditions are met

## Design

```python
def needs_transformation(data: Any) -> bool:
    """
    Check if an MCP response needs structuredContent transformation.
    
    A response needs transformation if it has a 'result' dict with 'content'
    but is missing the 'structuredContent' field.
    
    Args:
        data: The parsed JSON data to check.
        
    Returns:
        True if the response needs transformation, False otherwise.
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
