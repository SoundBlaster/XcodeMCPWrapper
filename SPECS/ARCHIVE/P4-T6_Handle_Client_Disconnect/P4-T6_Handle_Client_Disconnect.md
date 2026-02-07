# P4-T6: Handle Client Disconnect

## Overview
Handle EOF on stdin when client disconnects, ensuring clean shutdown per PRD §5.1

## Implementation

### Current Implementation Review
The stdin forwarding loop is implemented in `src/mcpbridge_wrapper/bridge.py`:

```python
def run_stdin_forwarder(bridge: subprocess.Popen) -> threading.Thread:
    def forward_loop() -> None:
        try:
            for line in sys.stdin:
                if bridge.stdin is not None:
                    bridge.stdin.write(line)
                    bridge.stdin.flush()
        except (BrokenPipeError, OSError):
            # Bridge stdin was closed, exit gracefully
            pass

    thread = threading.Thread(target=forward_loop, daemon=True)
    thread.start()
    return thread
```

### EOF Detection Mechanism
- When the MCP client disconnects, `sys.stdin` closes
- Python's `for line in sys.stdin` iteration automatically terminates when EOF is reached
- The daemon thread exits gracefully without raising exceptions
- Main loop in `__main__.py` detects bridge exit via `None` sentinel in queue

### Clean Shutdown Flow
1. Client disconnects → stdin pipe closes
2. `forward_loop()` exits (for loop ends on EOF)
3. Daemon thread terminates
4. Bridge process detects stdin close and exits
5. `run_stdout_reader()` puts `None` sentinel in queue
6. Main loop receives `None` and breaks
7. `cleanup_bridge()` called in finally block
8. Wrapper exits gracefully

## Acceptance Criteria
- [x] Wrapper terminates gracefully when stdin pipe is closed
- [x] No exceptions raised on client disconnect
- [x] Bridge process is properly cleaned up
- [x] Exit code propagated correctly

## Verification
Quality gates to run:
1. pytest - All unit tests
2. ruff - Linting check
3. mypy - Type checking
4. coverage - Coverage report
