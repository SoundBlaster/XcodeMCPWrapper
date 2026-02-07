# P4-T3: Handle Already Compliant Responses

## Overview

Ensure that responses which already contain a `structuredContent` field are passed through without modification, avoiding double-processing and potential data corruption.

## Requirements

### Functional Requirements

1. **FR1:** Detect when a response already has `structuredContent` field
2. **FR2:** Pass through such responses completely unchanged
3. **FR3:** Do not inject an additional `structuredContent` field

## Implementation Plan

### 1. Update `needs_transformation()` function

Location: `src/mcpbridge_wrapper/transform.py`

Add a check at the beginning of the function to detect existing `structuredContent`:

```python
def needs_transformation(result: dict) -> bool:
    """Check if a result object needs structuredContent injection."""
    # Already compliant - pass through unchanged
    if "structuredContent" in result:
        return False
    
    # Existing checks continue...
    if "content" not in result:
        return False
    
    content = result.get("content", [])
    if not isinstance(content, list) or len(content) == 0:
        return False
    
    return True
```

### 2. Add Unit Test

Location: `tests/unit/test_transform.py`

Add test case:

```python
def test_already_compliant_response():
    """Test that responses with structuredContent are not modified."""
    input_line = json.dumps({
        "result": {
            "content": [{"type": "text", "text": "data"}],
            "structuredContent": {"already": "present"}
        }
    })
    
    output_line = process_response_line(input_line)
    
    # Output should be identical to input
    assert json.loads(output_line) == json.loads(input_line)
```

## Acceptance Criteria

- [ ] Responses with existing `structuredContent` are passed through unchanged
- [ ] No duplicate `structuredContent` fields are created
- [ ] Unit test passes
- [ ] Coverage remains ≥90%

## Testing

1. Run unit tests: `pytest tests/unit/test_transform.py -v`
2. Run coverage: `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`
3. Verify all quality gates pass

## Related

- PRD §5.2 EC2: Already Compliant Responses
- P3-T3: Detect Non-Compliant Responses (dependency)

---
**Archived:** 2026-02-08
**Verdict:** PASS
