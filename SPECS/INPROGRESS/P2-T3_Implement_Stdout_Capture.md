# PRD: P2-T3 - Implement Stdout Capture with Line Buffering

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T3 |
| Task Name | Implement Stdout Capture with Line Buffering |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P0 |
| Dependencies | P2-T1 |

## Objective
Implement a generator function that reads stdout from the bridge process line-by-line with proper line buffering, ensuring complete lines are yielded for downstream processing.

## Requirements

### Functional Requirements
1. Create `read_stdout()` generator function that yields complete lines
2. Use line buffering (bufsize=1 already configured in Popen)
3. Each yielded item must be a complete line (ends with newline)
4. Handle EOF gracefully (stop iteration when no more data)
5. Pass through lines unmodified (no transformation)

### Interface Specification
```python
def read_stdout(bridge: subprocess.Popen) -> Generator[str, None, None]:
    """
    Generator that yields complete lines from bridge stdout.
    
    Args:
        bridge: The Popen bridge process with readable stdout
        
    Yields:
        Complete lines from stdout (each ends with newline, except possibly last)
        
    Example:
        >>> bridge = create_bridge()
        >>> for line in read_stdout(bridge):
        ...     print(line, end='')
    """
```

## Deliverables
1. Updated `src/mcpbridge_wrapper/bridge.py` - Add `read_stdout()` generator
2. Updated `src/mcpbridge_wrapper/__main__.py` - Use generator instead of single line read
3. Unit tests in `tests/unit/test_bridge.py` - Test stdout capture

## Acceptance Criteria
- [ ] Each yielded item is a complete line (ends with newline)
- [ ] No partial line buffering issues
- [ ] EOF handled correctly (generator stops)
- [ ] Generator yields unmodified lines
- [ ] Unit tests verify generator behavior

## Implementation Notes
- Use `iter(bridge.stdout.readline, '')` pattern for clean generator
- The Popen is already configured with `bufsize=1` for line buffering
- Empty string from readline indicates EOF
- Consider handling the case where bridge.stdout might be None
