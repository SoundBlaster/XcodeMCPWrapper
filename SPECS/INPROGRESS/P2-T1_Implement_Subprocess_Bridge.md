# PRD: P2-T1 - Implement Subprocess Bridge to xcrun mcpbridge

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T1 |
| Task Name | Implement Subprocess Bridge to xcrun mcpbridge |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P0 |
| Dependencies | P1-T1 |

## Objective
Create a subprocess.Popen wrapper that launches `xcrun mcpbridge` with bidirectional stdin/stdout pipes, establishing the foundation for the protocol compatibility wrapper.

## Requirements

### Functional Requirements
1. Create `create_bridge()` function in `src/mcpbridge_wrapper/bridge.py`
2. Use `subprocess.Popen` to launch `xcrun mcpbridge`
3. Configure stdin=PIPE, stdout=PIPE for bidirectional communication
4. Pass stderr through to wrapper's stderr (unmodified)
5. Support forwarding command-line arguments to mcpbridge

### Interface Specification
```python
def create_bridge(args: List[str] = None) -> subprocess.Popen:
    """
    Create a subprocess bridge to xcrun mcpbridge.
    
    Args:
        args: Additional arguments to pass to mcpbridge
        
    Returns:
        Popen object with readable stdout and writable stdin
    """
```

## Deliverables
1. `src/mcpbridge_wrapper/bridge.py` - New module with bridge functionality
2. Updated `src/mcpbridge_wrapper/__init__.py` - Export bridge module
3. Unit tests in `tests/unit/test_bridge.py`

## Acceptance Criteria
- [ ] Function returns a Popen object with readable stdout and writable stdin
- [ ] Process starts without errors when Xcode is running
- [ ] Command-line arguments are forwarded to mcpbridge
- [ ] stderr is passed through unmodified
- [ ] Unit tests verify Popen object creation and pipe configuration

## Implementation Notes
- Use `text=True` for line-based text processing
- Use `bufsize=1` for line buffering
- Import from typing for type hints
- Handle cases where xcrun/mcpbridge might not be available (for testing)
