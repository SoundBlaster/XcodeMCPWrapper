# PRD: P5-T2 Write Test for Valid Transformation (TC1)

## Task Information
- **Task ID:** P5-T2
- **Phase:** 5 - Testing & Verification
- **Priority:** P0
- **Status:** Implementation Already Complete

## Description
Test response with content, no structuredContent gets injected per PRD §7.1 TC1.

## Background
Per the main PRD §7.1, TC1 specifies:
> **TC1: Valid transformation case** - Input: JSON with `result.content` array containing text items, no `structuredContent`. Expected: `structuredContent` field injected with parsed JSON from text content.

## Test Case Specification

### TC1: Valid JSON Response Transformation

**Input:**
```json
{
  "result": {
    "content": [
      {"type": "text", "text": "{\"status\": \"ok\"}"}
    ]
  }
}
```

**Expected Output:**
```json
{
  "result": {
    "content": [
      {"type": "text", "text": "{\"status\": \"ok\"}"}
    ],
    "structuredContent": {"status": "ok"}
  }
}
```

**Validation Criteria:**
1. Output is valid JSON
2. Original `content` array is preserved
3. New `structuredContent` field is added
4. `structuredContent` contains parsed JSON from text content

## Implementation

The test is implemented in `tests/unit/test_transform.py`:

```python
def test_json_needing_transformation(self) -> None:
    """Should transform JSON that needs structuredContent."""
    line = '{"result": {"content": [{"type": "text", "text": "{\\"status\\": \\"ok\\"}"}]}}'
    result = process_response_line(line)
    parsed = json.loads(result)
    assert "structuredContent" in parsed["result"]
    assert parsed["result"]["structuredContent"] == {"status": "ok"}
```

## Test Coverage

- Function under test: `process_response_line()`
- Module: `mcpbridge_wrapper.transform`
- Coverage requirement: Covers main transformation path

## Dependencies

- P3-T7 [DONE] - Inject structuredContent into Result
- P5-T1 [DONE] - Create Unit Test Framework

## Acceptance Criteria

- [x] Test exists in `tests/unit/test_transform.py`
- [x] Test validates `structuredContent` injection
- [x] Test passes with current implementation
- [x] Coverage includes `process_response_line` function

## Notes

This test validates the core functionality of the wrapper - transforming non-compliant
MCP responses from xcrun mcpbridge into spec-compliant responses by injecting the
required `structuredContent` field.

---
**Archived:** 2026-02-11
**Verdict:** PASS
