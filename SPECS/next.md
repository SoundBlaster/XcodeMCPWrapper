# Current Task

## P5-T4: Write Test for Non-JSON Text Content (TC3)

**Status:** IN PROGRESS  
**Selected:** 2026-02-08  
**Phase:** 5 - Testing & Verification  
**Priority:** P0

### Description
Test fallback to `{"text": content}` wrapper per PRD §7.1 TC3

### Dependencies
- P3-T6 [DONE] - Implement Fallback Wrapper for Invalid JSON
- P5-T1 [DONE] - Create Unit Test Framework

### Acceptance Criteria
- [x] `structuredContent` equals `{"text": "plain text"}` for non-JSON content
- [x] `test_json_with_non_json_text_content` test exists and passes

### Implementation Notes
Test already implemented in `tests/unit/test_transform.py`:
- `TestProcessResponseLine::test_json_with_non_json_text_content`
- `TestParseStructuredContentWithFallback::test_non_json_text_gets_wrapped`

The test verifies that when text content is not valid JSON, it gets wrapped in `{"text": ...}` structure.
