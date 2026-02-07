# PRD: P2-T4 - Add Daemon Thread for Async Stdout Reading

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T4 |
| Task Name | Add Daemon Thread for Async Stdout Reading |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P0 |
| Dependencies | P2-T3 |

## Objective
Implement a daemon thread that asynchronously reads stdout from the bridge process and places lines into a thread-safe queue, allowing the main thread to process responses without blocking on I/O.

## Requirements

### Functional Requirements
1. Create `run_stdout_reader()` function that starts a daemon thread
2. Use `queue.Queue` for thread-safe line passing between threads
3. Thread continuously reads lines from bridge stdout
4. Lines are placed in queue for main thread consumption
5. Thread terminates automatically when bridge exits (daemon thread)
6. Handle EOF gracefully (stop reading when bridge closes stdout)

### Interface Specification
```python
def run_stdout_reader(bridge: subprocess.Popen) -> Tuple[threading.Thread, queue.Queue]:
    """
    Start a daemon thread that reads bridge stdout into a queue.
    
    Args:
        bridge: The Popen bridge process with readable stdout
        
    Returns:
        Tuple of (thread, queue) where queue contains lines from stdout
        
    Example:
        >>> bridge = create_bridge()
        >>> thread, output_queue = run_stdout_reader(bridge)
        >>> # Main thread can now process from queue without blocking
        >>> line = output_queue.get(timeout=1.0)
    """
```

## Deliverables
1. Updated `src/mcpbridge_wrapper/bridge.py` - Add stdout reader thread function
2. Updated `src/mcpbridge_wrapper/__main__.py` - Use async stdout reading
3. Unit tests in `tests/unit/test_bridge.py` - Test stdout reader thread

## Acceptance Criteria
- [ ] Main thread can continue processing while stdout is being read
- [ ] Thread terminates when bridge exits
- [ ] Thread is a daemon (doesn't prevent program exit)
- [ ] Queue provides thread-safe line passing
- [ ] EOF is handled gracefully (thread stops reading)
- [ ] Unit tests verify async behavior

## Implementation Notes
- Use `queue.Queue` with appropriate maxsize (0 for unlimited, or small buffer)
- Use `queue.put()` in reader thread, `queue.get()` in main thread
- Handle `queue.Empty` for non-blocking get operations
- Thread should catch exceptions and exit cleanly
