# PRD: P3-T1 - Implement JSON Detection Logic

**Task ID:** P3-T1  
**Task Name:** Implement JSON Detection Logic  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P0

---

## Overview

Implement a utility function `is_json_line()` that determines whether a given line of text is valid JSON or plain text. This is a foundational component for the response transformation engine that processes MCP bridge output.

## Requirements

### Functional Requirements (from PRD §3.1 FR3)

- Detect whether a line is valid JSON or plain text
- Must handle JSON objects, arrays, and primitives
- Must correctly identify non-JSON plain text

## Deliverables

### Code Changes

1. Create `src/mcpbridge_wrapper/transform.py` with `is_json_line()` function

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Valid JSON object detection
   - Valid JSON array detection
   - Valid JSON primitive detection (string, number, boolean, null)
   - Plain text rejection
   - Edge cases (empty string, whitespace-only)

## Acceptance Criteria

- [ ] `is_json_line('{"key": "value"}')` returns `True`
- [ ] `is_json_line('Plain text log')` returns `False`
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new module
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P2-T3 [✓ DONE] - Implement Stdout Capture with Line Buffering

## Implementation Notes

The function should:
1. Attempt to parse the line using `json.loads()`
2. Return `True` if parsing succeeds
3. Return `False` if parsing fails (JSONDecodeError)
4. Handle edge cases like empty strings and whitespace-only lines

## Design

```python
def is_json_line(line: str) -> bool:
    """
    Detect whether a line is valid JSON or plain text.
    
    Args:
        line: The input line to check.
        
    Returns:
        True if the line is valid JSON, False otherwise.
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
