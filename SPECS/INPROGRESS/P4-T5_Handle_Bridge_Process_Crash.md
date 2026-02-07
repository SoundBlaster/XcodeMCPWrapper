# P4-T5: Handle Bridge Process Crash

## Overview

Handle when `xcrun mcpbridge` process crashes or exits unexpectedly. The wrapper must detect bridge process termination and exit with the same exit code, ensuring proper error propagation to the parent process (MCP client).

This addresses the PRD §5.1 Error Handling Matrix requirement:
> | Scenario | Handling | Expected Behavior |
> |----------|----------|-------------------|
> | Bridge process crashes | Propagate exit | Wrapper exits with same code |

## Requirements

1. **Monitor Bridge Process**: Detect when the mcpbridge subprocess terminates unexpectedly
2. **Propagate Exit Code**: Return the exact exit code from mcpbridge to the wrapper's parent
3. **Clean Shutdown**: Ensure all resources are properly released before exiting
4. **No Zombie Processes**: Properly reap the subprocess to prevent defunct processes

## Current Implementation Analysis

### Existing Code in `src/mcpbridge_wrapper/bridge.py`

1. **`cleanup_bridge()`** (lines 122-168): Already handles:
   - Closing stdin to signal EOF
   - Waiting for process termination with optional timeout
   - Forceful termination/kill if needed
   - Returns `bridge.returncode`

2. **`run_stdout_reader()`** (lines 207-249): Already handles:
   - Reading stdout in daemon thread
   - Putting lines into thread-safe queue
   - Putting `None` sentinel when EOF reached

### Existing Code in `src/mcpbridge_wrapper/__main__.py`

1. **Main loop** (lines 51-76): Currently:
   - Initializes `exit_code = 0`
   - Processes lines from queue until `None` sentinel
   - Calls `cleanup_bridge()` in `finally` block
   - Returns exit code

### Gap Analysis

The current implementation has basic exit code handling but needs improvement:

1. **Early Detection**: The main loop only detects bridge termination when the stdout reader puts `None` in the queue. It should also poll `bridge.poll()` to detect crashes sooner.

2. **Exit Code Verification**: Need to verify that `cleanup_bridge()` returns the correct exit code even when the bridge has already terminated (not just during graceful shutdown).

3. **Crash vs Graceful Exit**: Currently doesn't distinguish between:
   - Bridge exiting normally with code 0
   - Bridge crashing with non-zero code
   - Bridge being killed by signal

## Implementation Plan

### 1. Enhance `src/mcpbridge_wrapper/__main__.py`

Modify the main loop to:
- Periodically check `bridge.poll()` during queue processing
- Capture exit code immediately when bridge terminates
- Ensure exit code is returned even if cleanup_bridge encounters errors

```python
# Key changes needed:
# - Check bridge.poll() after processing each line
# - Store exit_code when poll() returns non-None
# - Break loop early if bridge has terminated
```

### 2. Enhance `src/mcpbridge_wrapper/bridge.py` (if needed)

Verify `cleanup_bridge()` behavior:
- Ensure it returns correct exit code for already-terminated processes
- Ensure it doesn't mask the exit code with its own error handling

### 3. Add Exit Code Propagation Test

Create test to verify:
- Mock bridge that exits with code 1
- Wrapper exits with code 1
- No hanging or incorrect exit codes

## Acceptance Criteria

- [ ] When mcpbridge exits with code 1, wrapper also exits with code 1
- [ ] When mcpbridge exits with code 0, wrapper exits with code 0
- [ ] Exit codes from signals (e.g., 139 for SIGSEGV) are propagated correctly
- [ ] No zombie processes left after wrapper exits
- [ ] Wrapper exits promptly after bridge termination (no long delays)

## Testing Plan

### Unit Test

Create `tests/unit/test_bridge_crash.py`:

```python
def test_exit_code_propagation():
    """Test that wrapper exits with same code as bridge."""
    # Mock bridge process that exits with code 1
    # Run wrapper main loop
    # Assert exit code is 1
```

### Integration Test

Create `tests/integration/test_exit_code.py`:

```python
def test_bridge_crash_exit_code():
    """Test exit code propagation with real subprocess."""
    # Create mock bridge script that exits with specific code
    # Run wrapper with mock bridge
    # Verify wrapper exits with same code
```

### Manual Test

1. Start wrapper with Xcode running
2. Kill mcpbridge process manually (`pkill mcpbridge`)
3. Verify wrapper exits with code matching how mcpbridge was killed

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Bridge exits 0 (normal) | Wrapper exits 0 |
| Bridge exits 1 (error) | Wrapper exits 1 |
| Bridge killed by SIGTERM | Wrapper exits 143 (128+15) |
| Bridge killed by SIGKILL | Wrapper exits 137 (128+9) |
| Bridge segfaults | Wrapper exits 139 (128+11) |
| Cleanup fails | Still return bridge exit code if known |

## References

- PRD §5.1: Error Handling Matrix
- PRD §5.1: "Bridge process crashes | Propagate exit | Wrapper exits with same code"
- `src/mcpbridge_wrapper/bridge.py`: `cleanup_bridge()` function
- `src/mcpbridge_wrapper/__main__.py`: Main entry point and loop
