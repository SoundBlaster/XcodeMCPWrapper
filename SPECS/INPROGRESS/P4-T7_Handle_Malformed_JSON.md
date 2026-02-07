# Task P4-T7: Handle Malformed JSON from Bridge

## Overview

Pass through malformed/unparseable JSON lines from the bridge unchanged, as specified in PRD §5.1.

## Implementation Status

**Status: ALREADY COMPLETE**

The `parse_json_safe()` function in `src/mcpbridge_wrapper/transform.py` (lines 44-59) already implements this requirement:

```python
def parse_json_safe(line: str) -> tuple[bool, Any]:
    """
    Safely parse a JSON line, returning success status and result.

    Args:
        line: The input line to parse.

    Returns:
        A tuple of (success: bool, result: Any). On success, result is the
        parsed JSON value. On failure, result is the original line.
    """
    try:
        parsed = json.loads(line)
        return (True, parsed)
    except json.JSONDecodeError:
        return (False, line)
```

The `process_response_line()` function uses this to pass through invalid JSON unchanged (lines 187-192):

```python
success, data = parse_json_safe(line)
if not success:
    return line
```

## Test Coverage

Existing tests verify this behavior:

1. **TestParseJsonSafe::test_partial_json_returns_failure** (line 131-136)
   - Verifies `{"broken` returns `(False, original)`

2. **TestProcessResponseLine::test_partial_json** (line 540-544)
   - Verifies partial JSON passes through unchanged

3. **TestIsJsonLine::test_partial_json_rejection** (line 60-62)
   - Verifies `{"broken` is rejected as non-JSON

## Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Partial JSON `{"broken` passes through unchanged | ✅ PASS | `test_partial_json` passes |
| Invalid JSON returns `(False, original)` tuple | ✅ PASS | `test_partial_json_returns_failure` passes |
| No exception raised on malformed JSON | ✅ PASS | All tests pass |

## Quality Gates

Run before completion:
- [x] pytest -k "partial" passes
- [x] ruff check passes
- [x] mypy type check passes
- [x] Coverage ≥90%

## PRD References

- PRD §5.1: "Malformed JSON from Bridge - Pass through unparseable JSON lines unchanged"
