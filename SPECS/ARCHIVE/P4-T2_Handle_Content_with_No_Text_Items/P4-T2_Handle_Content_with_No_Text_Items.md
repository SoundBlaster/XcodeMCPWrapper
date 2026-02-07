# P4-T2: Handle Content with No Text Items

**Task ID:** P4-T2  
**Priority:** P1  
**Phase:** 4 - Edge Case Handling

## Overview

Ensure that MCP responses containing only image or non-text content types pass through without transformation. This handles the edge case where `structuredContent` cannot be extracted because there is no text content to parse.

## Background

Per PRD §5.2 EC3, when an MCP response has a content array with only non-text items (like images), the wrapper should not attempt to inject a `structuredContent` field. This is different from empty content (P4-T1) - there is content, but it's not transformable.

## Requirements

### Functional Requirements

- FR1: Content arrays with only image items must pass through unchanged
- FR2: Content arrays with only non-text types must pass through unchanged
- FR3: `extract_text_content()` must return `None` when no text items exist
- FR4: `inject_structured_content()` must not modify data when text extraction returns `None`
- FR5: `needs_transformation()` must return `False` when content has no transformable text

## Implementation

### Current State

The implementation is already complete in `src/mcpbridge_wrapper/transform.py`:

1. `extract_text_content()` (lines 92-107): Returns `None` when no text items found
2. `inject_structured_content()` (lines 142-166): Returns early when `text is None`
3. `needs_transformation()` (lines 62-89): Returns `False` for empty content (already handled)

### Missing Test Coverage

While unit tests exist for the individual functions, an explicit end-to-end test case for image-only content in `process_response_line()` is needed for complete verification.

## Acceptance Criteria

- [ ] AC1: `[{"type": "image", "url": "..."}]` content results in no transformation
- [ ] AC2: Mixed image-only content arrays pass through unchanged
- [ ] AC3: `process_response_line()` returns original JSON for image-only responses
- [ ] AC4: No `structuredContent` field is injected when no text content exists
- [ ] AC5: Test coverage for this edge case is ≥90%

## Test Cases

### TC1: Image-Only Content (EC3)
**Input:**
```json
{"result": {"content": [{"type": "image", "url": "http://example.com/img.png"}]}}
```

**Expected Output:**
```json
{"result": {"content": [{"type": "image", "url": "http://example.com/img.png"}]}}
```

**Verification:** Output JSON equals input JSON exactly (no transformation)

### TC2: Multiple Image Items
**Input:**
```json
{"result": {"content": [{"type": "image", "url": "img1.png"}, {"type": "image", "url": "img2.png"}]}}
```

**Expected Output:** Same as input (no structuredContent added)

### TC3: Other Non-Text Types
**Input:**
```json
{"result": {"content": [{"type": "file", "path": "/tmp/data.bin"}]}}
```

**Expected Output:** Same as input (no structuredContent added)

## Files to Modify

- `tests/unit/test_transform.py` - Add explicit test cases for image-only passthrough

## Dependencies

- P3-T4: Extract Text from Content Array [✓ DONE]

## Workflow

SELECT → PLAN → EXECUTE → ARCHIVE

---
**Archived:** 2026-02-07
**Verdict:** PASS
