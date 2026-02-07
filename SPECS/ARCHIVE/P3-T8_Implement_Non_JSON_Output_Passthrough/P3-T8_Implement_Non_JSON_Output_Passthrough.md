# PRD: P3-T8 - Implement Non-JSON Output Passthrough

**Task ID:** P3-T8  
**Task Name:** Implement Non-JSON Output Passthrough  
**Phase:** Phase 3 - Response Transformation Engine  
**Priority:** P1

---

## Overview

Implement a function `process_response_line()` that handles both JSON and non-JSON lines from the MCP bridge. Non-JSON lines (logs, errors) should be passed through unchanged, while JSON lines that need transformation should be processed and modified.

## Requirements

### Functional Requirements (from PRD §3.1 FR8)

- Pass through non-JSON lines (logs, errors) unmodified
- Transform JSON lines that need transformation
- Return processed line for output

## Deliverables

### Code Changes

1. Add `process_response_line()` function to `src/mcpbridge_wrapper/transform.py`

### Test Coverage

1. Unit tests in `tests/unit/test_transform.py` covering:
   - Non-JSON plain text passthrough
   - JSON lines that need transformation
   - JSON lines that don't need transformation (already compliant)
   - Empty line handling

## Acceptance Criteria

- [ ] `process_response_line("log message")` returns `"log message"` unchanged
- [ ] JSON line needing transformation returns transformed JSON string
- [ ] All unit tests pass
- [ ] Code coverage ≥90% for the new function
- [ ] `ruff check src/` passes with no errors

## Dependencies

- P3-T1 [✓ DONE] - Implement JSON Detection Logic

## Implementation Notes

The function should:
1. Check if line is valid JSON using `is_json_line()`
2. If not JSON, return the line unchanged
3. If JSON, parse and check if transformation is needed
4. If transformation needed, inject structuredContent and return JSON string
5. If already compliant, return original line

## Design

```python
def process_response_line(line: str) -> str:
    """
    Process a single response line from the MCP bridge.

    Non-JSON lines are passed through unchanged.
    JSON lines that need transformation are modified to add structuredContent.

    Args:
        line: The response line to process.

    Returns:
        The processed line (transformed JSON or original non-JSON).
    """
```

---
**Archived:** 2026-02-07
**Verdict:** PASS
