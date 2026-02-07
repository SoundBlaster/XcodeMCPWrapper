# PRD: P2-T6 - Handle Bridge Process Lifecycle

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T6 |
| Task Name | Handle Bridge Process Lifecycle |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P1 |
| Dependencies | P2-T1 |

## Objective
Implement proper lifecycle management for the bridge subprocess including startup verification, clean shutdown on exit, and exit code propagation to ensure no zombie processes and correct exit behavior.

## Requirements

### Functional Requirements
1. **Startup Verification:** Verify bridge process started successfully (poll() returns None)
2. **Clean Shutdown:** Close stdin, wait for process termination
3. **Exit Code Propagation:** Return bridge's exit code from cleanup function
4. **Signal Handling:** Handle SIGTERM/SIGINT gracefully (already in __main__.py)
5. **No Zombie Processes:** Always call wait() on subprocess

### Interface Specification
```python
def verify_bridge_started(bridge: subprocess.Popen) -> bool:
    """
    Verify that the bridge process started successfully.
    
    Args:
        bridge: The Popen bridge process
        
    Returns:
        True if process is running, False if it failed to start
    """

def cleanup_bridge(bridge: subprocess.Popen, timeout: Optional[float] = None) -> int:
    """
    Clean up the bridge process and return its exit code.
    
    Args:
        bridge: The Popen bridge process
        timeout: Optional timeout in seconds to wait for termination
        
    Returns:
        Exit code of the bridge process
    """
```

## Deliverables
1. Updated `src/mcpbridge_wrapper/bridge.py` - Add startup verification
2. Updated `src/mcpbridge_wrapper/__main__.py` - Use lifecycle functions
3. Unit tests in `tests/unit/test_bridge.py` - Test lifecycle management

## Acceptance Criteria
- [ ] Wrapper exits with same code as mcpbridge
- [ ] No zombie processes left (wait() called)
- [ ] Startup verification confirms process is running
- [ ] Clean shutdown closes stdin and waits for termination
- [ ] Unit tests verify lifecycle behavior

## Implementation Notes
- `poll()` returns None if process is still running
- `wait()` is required to prevent zombie processes
- Close stdin before waiting to signal EOF to bridge
- Use timeout in wait() for graceful shutdown with fallback to kill()
