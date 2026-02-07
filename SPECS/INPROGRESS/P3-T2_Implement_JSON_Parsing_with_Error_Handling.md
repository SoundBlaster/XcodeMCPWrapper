# PRD: P3-T2 - Implement JSON Parsing with Error Handling

**Task ID:** P3-T2  
**Task Name:** Implement JSON Parsing with Error Handling  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a safe JSON parsing function `parse_json_safe()` that returns a tuple indicating success/failure along with either the parsed data or the original line. This provides a non-exception-based interface for parsing JSON responses.

## Requirements

### Functional Requirements (from PRD §3.1 FR3)

- Parse JSON lines with try/except error handling
- Return structured result instead of raising exceptions
- Preserve original line on parse failure

## Deliverables

### Code Changes

1. Add `parse_json_safe()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Valid JSON object parsing
   - Valid JSON array parsing
   - Valid JSON primitive parsing
   - Invalid JSON handling
   - Empty string handling
   - Whitespace-only handling

## Acceptance Criteria

- [ ] `parse_json_safe('{"key": "value"}')` returns `(True, {"key": "value"})`
- [ ] `parse_json_safe('invalid json')` returns `(False, 'invalid json')`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T1 [✓ DONE] - Implement JSON Detection Logic

## Implementation Notes

The function should:
1. Attempt to parse the line using `json.loads()`
2. Return `(True, parsed_data)` on success
3. Return `(False, original_line)` on failure
4. Be type-hinted for clarity

## Design

```python
def parse_json_safe(line: str) -> tuple[bool, Union[dict, list, str, int, float, bool, None, str]]:
    """
    Safely parse a JSON line, returning success status and result.
    
    Args:
        line: The input line to parse.
        
    Returns:
        A tuple of (success: bool, result: Any). On success, result is the
        parsed JSON value. On failure, result is the original line.
    """
```
