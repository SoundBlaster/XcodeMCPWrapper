# Task P4-T1: Handle Empty Content Array

## Metadata

| Field | Value |
|-------|-------|
| **Task ID** | P4-T1 |
| **Task Name** | Handle Empty Content Array |
| **Phase** | Phase 4 - Edge Case Handling |
| **Priority** | P1 |
| **Status** | IN PROGRESS |
| **Started** | 2026-02-07 |

## Description

Pass through responses with `"content": []` without modification per PRD §5.1.

## Problem Statement

The current `needs_transformation()` function returns `True` for responses with an empty content array because it only checks if the 'content' key exists in the result, not if the content array has any items. According to the PRD §5.1, responses with empty content arrays should be passed through unchanged since there's no text content to extract and parse into `structuredContent`.

## Current Behavior

```python
data = {"result": {"content": []}}
needs_transformation(data)  # Returns True (incorrect)
```

The function currently checks:
1. Is `data` a dict? ✓
2. Is `result` a dict? ✓
3. Does `result` have `content`? ✓
4. Does `result` lack `structuredContent`? ✓ → Returns True

## Desired Behavior

```python
data = {"result": {"content": []}}
needs_transformation(data)  # Should return False
```

The function should additionally check:
5. Is `content` a non-empty list? If empty, return False

## Implementation Plan

### Code Changes

Modify `src/mcpbridge_wrapper/transform.py`:

**Current `needs_transformation()` logic:**
```python
if "content" not in result:
    return False
return "structuredContent" not in result
```

**Updated logic:**
```python
if "content" not in result:
    return False

content = result.get("content")
if isinstance(content, list) and len(content) == 0:
    return False

return "structuredContent" not in result
```

### Test Changes

Update `tests/unit/test_transform.py`:

The existing test `test_with_empty_content_array` currently expects `True` but should expect `False`:

```python
def test_with_empty_content_array(self) -> None:
    """Should return False for empty content array (nothing to transform)."""
    data = {"result": {"content": []}}
    assert needs_transformation(data) is False  # Changed from True
```

## Acceptance Criteria

- [ ] `needs_transformation({"result": {"content": []}})` returns `False`
- [ ] Empty content arrays are passed through unchanged
- [ ] All existing tests continue to pass
- [ ] All quality gates pass:
  - `pytest tests/unit/test_transform.py -v` - all tests pass
  - `ruff check src/` - no linting errors
  - `pytest --cov=mcpbridge_wrapper.transform` - coverage ≥90%

## Dependencies

- P3-T3 [✓ DONE] - Detect Non-Compliant Responses

## References

- PRD §5.1: "Empty content array" edge case handling
- PRD §5.2 EC3: Content with no text items
