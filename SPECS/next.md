# Current Task

## P4-T5: Handle Bridge Process Crash

**Status:** IN PROGRESS  
**Selected:** 2026-02-08  
**Phase:** 4 - Edge Case Handling  
**Priority:** P1

### Description
Detect bridge process termination and exit with same exit code per PRD §5.1

### Dependencies
- P2-T6 [DONE] - Handle Bridge Process Lifecycle

### Acceptance Criteria
- [ ] When mcpbridge exits with code 1, wrapper also exits with code 1
- [ ] Bridge process crash is detected promptly
- [ ] Exit code is propagated correctly to parent process

### Implementation Notes
- Check `src/mcpbridge_wrapper/bridge.py` for existing `cleanup_bridge()` function
- Review `src/mcpbridge_wrapper/__main__.py` for exit code handling in main loop
- PRD §5.1 requires: "Bridge process crashes | Propagate exit | Wrapper exits with same code"
