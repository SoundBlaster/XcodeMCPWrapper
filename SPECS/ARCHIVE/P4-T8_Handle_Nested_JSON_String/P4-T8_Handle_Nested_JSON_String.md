# Task Plan: P4-T8 - Handle Nested JSON String Content

## Overview

Handle JSON string primitives as valid structuredContent per PRD §5.2 EC4.

## PRD Reference

### PRD §5.2 EC4: Nested JSON String
```json
{
  "content": [{"type": "text", "text": "\"plain string\""}]
}
```
**Expected**: Parse as valid JSON string, inject as `structuredContent`

Result should be:
```json
{
  "content": [{"type": "text", "text": "\"plain string\""}],
  "structuredContent": "plain string"
}
```

## Implementation

The `parse_structured_content()` function in `src/mcpbridge_wrapper/transform.py` already handles this correctly:

```python
def parse_structured_content(text: str) -> Any:
    """
    Parse extracted text content as JSON.
    
    Returns:
        The parsed JSON value (dict, list, str, int, float, bool, or None).
    """
    return json.loads(text)
```

Python's `json.loads()` correctly parses all JSON types:
- Objects: `'{"key": "value"}'` → `{"key": "value"}`
- Arrays: `'[1, 2, 3]'` → `[1, 2, 3]`
- **String primitives**: `'"plain string"'` → `"plain string"` ✅
- Number primitives: `'42'` → `42`
- Boolean primitives: `'true'` → `True`
- Null: `'null'` → `None`

## Acceptance Criteria

1. ✅ Text `"plain string"` becomes `structuredContent: "plain string"` (not error)
2. ✅ Implementation uses `parse_structured_content()` via `json.loads()`
3. ✅ Test coverage exists for string primitive handling

## Test Coverage

Existing tests in `tests/unit/test_transform.py`:

1. `test_json_string_primitive` - Verifies `parse_structured_content('"plain string"')` returns `"plain string"`
2. `test_json_string_primitive_returns_string` - Verifies fallback wrapper also handles string primitives
3. `test_valid_json_string_primitive` (is_json_line) - Verifies detection
4. `test_valid_json_string_primitive` (parse_json_safe) - Verifies parsing

## Status

**Implementation**: Already complete in P3-T5
**Tests**: Already complete (multiple test cases)
**Validation**: Ready for quality gates
