---
**Archive Metadata:**
- **Task ID:** P3-T10
- **Task Name:** Implement Main Response Processing Loop
- **Status:** ✅ COMPLETED
- **Archive Date:** 2026-02-07
- **Verdict:** PASS
- **Commits:**
  - `6330039` - Implement P3-T10: Add main response processing loop with full integration
---

# P3-T10: Implement Main Response Processing Loop

## Overview

This task integrates all previously implemented components (subprocess bridge, response transformation, daemon threads) into a cohesive main entry point. The result is a complete end-to-end pipeline: stdin → bridge → transform → stdout.

## Requirements

Per PRD §4.2 Runtime Request/Response Flow:

1. **Stdin Forwarding**: Forward all MCP client requests to xcrun mcpbridge unmodified
2. **Stdout Processing**: Read bridge stdout, apply `process_response_line()` transformation
3. **Concurrent I/O**: Use daemon threads for bidirectional communication
4. **Unbuffered Output**: All output operations use `flush=True`
5. **Clean Shutdown**: Handle signals, propagate exit codes, no zombie processes

## Deliverables

### Code Files

1. **`src/mcpbridge_wrapper/__main__.py`** - Updated main() entry point with:
   - Bridge creation via `create_bridge()`
   - Stdin forwarding via `run_stdin_forwarder()` daemon thread
   - Stdout reading via `run_stdout_reader()` daemon thread
   - Response processing via `process_response_line()`
   - Unbuffered output to stdout
   - Proper cleanup via `cleanup_bridge()`
   - Signal handling for clean shutdown

2. **`src/mcpbridge_wrapper/__init__.py`** - Updated exports:
   - Add `process_response_line` to `__all__`
   - Ensure all public functions are importable

### Verification Files

- `SPECS/INPROGRESS/P3-T10_Validation_Report.md` - Quality gate results

## Test Coverage Requirements

Per PRD §7.1 Test Cases:

| TC | Test Case | Status Required |
|----|-----------|-----------------|
| TC1 | Valid transformation | PASS |
| TC2 | Already compliant | PASS |
| TC3 | Non-JSON text fallback | PASS |
| TC4 | Non-JSON line passthrough | PASS |
| TC5 | Empty content array | PASS |
| TC6 | No result field | PASS |

Per PRD §5.2 Edge Cases:

| EC | Edge Case | Status Required |
|----|-----------|-----------------|
| EC1 | Mixed content types | PASS |
| EC2 | Already compliant response | PASS |
| EC3 | Non-text content only | PASS |
| EC4 | Nested JSON string | PASS |

## Acceptance Criteria

- [ ] `__main__.py` integrates bridge and transform modules correctly
- [ ] Daemon threads handle concurrent I/O without blocking
- [ ] `process_response_line()` transforms responses before output
- [ ] All output uses `flush=True` (unbuffered)
- [ ] Exit code propagates from bridge to wrapper
- [ ] KeyboardInterrupt and signals handled gracefully
- [ ] All unit tests pass: `pytest tests/unit/test_transform.py -v`
- [ ] No linting errors: `ruff check src/`
- [ ] Coverage ≥90%: `pytest --cov=mcpbridge_wrapper`

## Implementation Notes

### Data Flow

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────►│   Wrapper    │────►│   Bridge    │     │   Wrapper    │────►│  Client  │
│  stdin   │     │  (forward)   │     │   stdin     │     │  (process)   │     │  stdout  │
└──────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └──────────┘
                                                      │
                                                      │     ┌──────────────┐
                                                      └────►│ process_response_line()
                                                            │ - is_json_line()
                                                            │ - parse_json_safe()
                                                            │ - needs_transformation()
                                                            │ - inject_structured_content()
                                                            └──────────────┘
```

### Thread Model

1. **Main Thread**: Processes stdout queue, transforms lines, outputs to client
2. **Stdin Forwarder Thread** (daemon): Reads client stdin, forwards to bridge
3. **Stdout Reader Thread** (daemon): Reads bridge stdout, puts to queue

### Signal Handling

- SIGINT/SIGTERM: Trigger clean shutdown
- Close bridge stdin to signal EOF
- Wait for bridge process with timeout
- Propagate exit code

### Error Handling

| Scenario | Handling |
|----------|----------|
| Bridge crashes | Propagate exit code |
| Client disconnect | Detect EOF, clean shutdown |
| Broken pipe | Graceful thread exit |
| Malformed JSON | Pass through unchanged |

## Dependencies

- `src/mcpbridge_wrapper/bridge.py` - Subprocess bridge functions
- `src/mcpbridge_wrapper/transform.py` - Response transformation functions
- `tests/unit/test_transform.py` - Existing test suite

## Related PRD Sections

- PRD §3.1 FR1-FR10: Functional requirements
- PRD §3.1 NFR1-NFR6: Non-functional requirements
- PRD §4.2: Runtime request/response flow
- PRD §5.1: Error handling scenarios
- PRD §5.2: Edge cases EC1-EC4
- PRD §7.1: Test cases TC1-TC6
