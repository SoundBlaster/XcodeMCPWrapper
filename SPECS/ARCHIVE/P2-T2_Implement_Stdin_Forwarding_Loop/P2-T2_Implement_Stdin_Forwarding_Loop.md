# PRD: P2-T2 - Implement Stdin Forwarding Loop

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T2 |
| Task Name | Implement Stdin Forwarding Loop |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P0 |
| Dependencies | P2-T1 |

## Objective
Implement a continuous stdin forwarding loop that reads lines from sys.stdin and forwards them unmodified to the bridge's stdin, enabling bidirectional MCP protocol communication.

## Requirements

### Functional Requirements
1. Create `run_stdin_forwarder()` function that continuously reads from sys.stdin
2. Forward each line to bridge.stdin immediately (line-by-line)
3. Handle EOF (client disconnect) gracefully
4. Preserve all bytes exactly (no modification)
5. Use unbuffered/flushed writes for real-time communication

### Interface Specification
```python
def run_stdin_forwarder(bridge: subprocess.Popen) -> None:
    """
    Continuously forward stdin lines to bridge stdin.
    
    Args:
        bridge: The Popen bridge process with writable stdin
        
    Note:
        This function blocks until EOF is reached on sys.stdin.
    """
```

## Deliverables
1. Updated `src/mcpbridge_wrapper/bridge.py` - Add stdin forwarding loop
2. `src/mcpbridge_wrapper/__main__.py` - Entry point with stdin forwarding
3. Unit tests in `tests/unit/test_bridge.py` - Test stdin forwarding

## Acceptance Criteria
- [ ] Raw bytes from sys.stdin appear identically on bridge.stdin
- [ ] Manual test with echo confirms passthrough
- [ ] EOF detection works correctly (graceful shutdown)
- [ ] Each line is flushed immediately to bridge
- [ ] Unit tests verify forwarding behavior

## Implementation Notes
- Use `for line in sys.stdin:` pattern for line-by-line reading
- Always flush after writing to ensure real-time communication
- Handle the case where bridge.stdin might be closed
- Consider running this in a separate thread to avoid blocking
