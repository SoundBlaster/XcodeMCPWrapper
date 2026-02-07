# PRD: Handle Responses Without Result Field

## Task Metadata
- **Task ID:** P4-T4
- **Task Name:** Handle Responses Without Result Field
- **Phase:** Phase 4
- **Priority:** P1

## Overview
Pass through JSON objects without a `result` key unchanged. This includes MCP notifications, error responses, and any other JSON messages that don't contain tool results.

## Background
MCP protocol includes various message types beyond tool results:
- **Notifications:** Messages like `{"jsonrpc": "2.0", "method": "notifications/initialized"}` with no `result` field
- **Error responses:** Messages like `{"id": 1, "error": {"code": -32600, "message": "Invalid Request"}}` 
- **Requests:** Client-to-server messages that also lack a `result` field

These messages must pass through the wrapper unchanged to maintain protocol integrity.

## Requirements

### Functional Requirements
1. Detect JSON objects that lack a `result` field
2. Pass such objects through without any transformation
3. Preserve original JSON formatting/whitespace (as much as possible)

### Non-Functional Requirements
- Processing overhead must remain < 5ms (NFR1)
- Must not log or modify error/notification content

## Implementation Plan

### Current Implementation
The `needs_transformation()` function in `src/mcpbridge_wrapper/transform.py` already handles this case correctly:

```python
def needs_transformation(data: Any) -> bool:
    if not isinstance(data, dict):
        return False

    result = data.get("result")
    if not isinstance(result, dict):  # <-- Returns False if no 'result' key
        return False
    # ... rest of checks
```

At line 78-79, `data.get("result")` returns `None` when the key doesn't exist, and `not isinstance(None, dict)` evaluates to `True`, causing the function to return `False`. This means no transformation is applied.

### Edge Cases Handled
- `{"jsonrpc": "2.0", "method": "initialized"}` - notification → passes through
- `{"id": 1, "error": null}` - error response → passes through  
- `{"id": 2, "error": {"code": -32600, "message": "Invalid Request"}}` - error with details → passes through
- `{"id": 3}` - response with neither result nor error → passes through

## Acceptance Criteria
1. Responses without `result` field pass through unchanged
2. `{"id": 1, "error": null}` is passed through unchanged (verified by test)
3. No transformation logic is executed for these messages

## Testing

### Existing Test Coverage
The current test suite already covers this case:
- `test_needs_transformation_no_result_field()` - Verifies that JSON without `result` returns `False`

### Running Tests
```bash
python3 -m pytest tests/unit/test_transform.py::test_needs_transformation_no_result_field -v
```

### Expected Test Output
```
tests/unit/test_transform.py::test_needs_transformation_no_result_field PASSED
```

## Verification

The implementation is already correct. The task is to verify that:
1. The existing code handles this case
2. Tests pass confirming the behavior

No code changes are required for this task.

## References
- `src/mcpbridge_wrapper/transform.py` - Lines 78-79 handle the missing `result` case
- `tests/unit/test_transform.py` - Contains existing test coverage
