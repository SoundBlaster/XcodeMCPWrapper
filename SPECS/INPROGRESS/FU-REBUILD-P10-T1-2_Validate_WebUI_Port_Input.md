# FU-REBUILD-P10-T1-2: Validate Web UI Port Input

## Summary
Add explicit validation for `--web-ui-port` CLI input and return clear errors for malformed or out-of-range values.

## Problem
The parser currently casts raw values with `int(...)`, which can surface unstructured `ValueError` behavior.

## Scope
- Add dedicated port parsing/validation helper.
- Enforce allowed port range.
- Convert parsing failures into user-facing stderr message and controlled non-zero exit code.
- Add unit tests for parser and `main()` error path.

## Deliverables
- `src/mcpbridge_wrapper/__main__.py`
- `tests/unit/test_main_webui.py`
- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-2_Validation_Report.md`

## Acceptance Criteria
- Invalid non-integer port values are rejected with explicit message.
- Out-of-range ports (e.g., `0`, `70000`) are rejected with explicit message.
- `main()` returns error exit code and does not start bridge on invalid port input.
- Existing tests remain green.
