# PRD: P2-T5 - Implement Stderr Passthrough

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T5 |
| Task Name | Implement Stderr Passthrough |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P1 |
| Dependencies | P2-T1 |

## Objective
Ensure stderr from the bridge subprocess is passed directly to the wrapper's stderr without modification, allowing error messages from mcpbridge to appear on the terminal immediately.

## Requirements

### Functional Requirements
1. Bridge subprocess stderr must be connected to wrapper's stderr
2. No buffering or modification of stderr output
3. Error messages appear immediately on terminal
4. No interference with stdout processing

### Implementation Note
This requirement was already implemented in P2-T1 via:
```python
subprocess.Popen(
    ...,
    stderr=sys.stderr,
    ...
)
```

This task focuses on verification and documentation.

## Deliverables
1. Verification tests in `tests/unit/test_bridge.py`
2. Documentation of stderr handling behavior

## Acceptance Criteria
- [ ] Error messages from mcpbridge appear on terminal immediately
- [ ] stderr is not captured or modified by the wrapper
- [ ] Tests verify stderr=sys.stderr is passed to Popen

## Implementation Notes
- Using `stderr=sys.stderr` in Popen inherits the parent's stderr file descriptor
- This is the simplest and most direct passthrough mechanism
- No additional threads or processing needed for stderr
