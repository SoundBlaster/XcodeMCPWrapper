# PRD: P2-T7 - Forward Command-Line Arguments

## Task Metadata
| Field | Value |
|-------|-------|
| Task ID | P2-T7 |
| Task Name | Forward Command-Line Arguments |
| Phase | Phase 2 - Core Bridge Implementation |
| Priority | P1 |
| Dependencies | P2-T1 |

## Objective
Ensure command-line arguments passed to the wrapper are forwarded to the mcpbridge subprocess, allowing users to pass any bridge arguments through the wrapper.

## Requirements

### Functional Requirements
1. Forward `sys.argv[1:]` to mcpbridge subprocess
2. Arguments should be passed unmodified
3. Empty argument list should be handled gracefully

### Implementation Note
This was already implemented in P2-T1 via the `args` parameter in `create_bridge()`. This task verifies the implementation.

## Deliverables
1. Verification tests in `tests/unit/test_bridge.py`

## Acceptance Criteria
- [ ] Running `wrapper --help` would show mcpbridge help output
- [ ] Arguments are passed unmodified to subprocess
- [ ] Tests verify argument forwarding

## Implementation Notes
- Already implemented in `create_bridge(args)` function
- Arguments are appended to the command list: `["xcrun", "mcpbridge"] + args`
