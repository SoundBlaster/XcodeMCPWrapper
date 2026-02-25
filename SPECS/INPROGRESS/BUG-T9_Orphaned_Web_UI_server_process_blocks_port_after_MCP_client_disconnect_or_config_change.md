# PRD: BUG-T9 — Orphaned Web UI server process blocks port after MCP client disconnect or config change

**Task ID:** BUG-T9  
**Priority:** P1  
**Phase:** Known Issues / Bug Tracker  
**Status:** Planned  
**Dependencies:** None

## Objective Summary

When an MCP client disconnects, the wrapper can remain alive because the main loop blocks on `output_queue.get()` while `xcrun mcpbridge` still owns stdout. This leaves the Web UI thread running and the configured port (for example `8080`) occupied by an orphaned process. The objective is to make wrapper shutdown deterministic when stdin reaches EOF by actively terminating the upstream bridge with a bounded timeout, so the stdout reader emits EOF and the main loop exits. The change must preserve normal request handling, avoid regressing existing broker/web-ui flows, and keep behavior cross-platform for supported Python environments.

## Deliverables

- Lifecycle update in `src/mcpbridge_wrapper/bridge.py` and `src/mcpbridge_wrapper/__main__.py` to react to stdin closure.
- New unit tests covering stdin-EOF shutdown behavior and forced-kill fallback behavior.
- Validation report documenting quality gates and bug-specific verification.

## Success Criteria and Acceptance Tests

1. Wrapper requests graceful upstream shutdown immediately after stdin reaches EOF.
2. If upstream does not exit within a configured grace window, wrapper escalates to force kill.
3. Main loop exits without hanging once EOF-driven shutdown is triggered.
4. Existing behavior for normal request/response handling is unchanged.
5. Unit tests prove:
   - EOF callback path is executed.
   - Graceful-then-force termination logic is invoked as expected.
   - Existing bridge forwarding tests still pass.

## Test-First Plan

1. Add failing unit test in `tests/unit/test_bridge.py` proving stdin forwarder emits a closure callback when stdin iteration ends.
2. Add failing unit test in `tests/unit/test_main.py` proving main wires an EOF callback that triggers bridge termination logic.
3. Add failing unit test for timeout escalation path (terminate then kill) via mocked bridge process.
4. Implement lifecycle changes in bridge/main modules.
5. Re-run targeted tests, then full required quality gates.

## TODO Plan

### Phase 1: EOF Signaling Hook

- **Inputs:** current `run_stdin_forwarder()` behavior, bug report root cause.
- **Outputs:** optional `on_stdin_closed` callback support and tests.
- **Verification:** callback invoked once on EOF and on write-error exit paths.

### Phase 2: Deterministic Upstream Termination

- **Inputs:** bridge subprocess handle, EOF signal from Phase 1.
- **Outputs:** helper that performs terminate -> wait(timeout) -> kill fallback.
- **Verification:** unit tests assert `terminate()` is called first and `kill()` only after timeout.

### Phase 3: Main-Loop Integration and Regression Safety

- **Inputs:** `main()` threading and cleanup flow.
- **Outputs:** EOF callback wiring in `main()` and regression tests.
- **Verification:** tests confirm no hang path and existing metrics/audit flow remains intact.

## Decision Points and Constraints

- Prefer a thread-safe callback approach over polling (`os.getppid`) to minimize runtime overhead and platform complexity.
- Keep shutdown idempotent: multiple EOF/error signals must not spam termination calls.
- Preserve current `cleanup_bridge()` finalizer behavior; new logic should unblock normal cleanup rather than replacing it.
- Avoid changing user-facing CLI flags in this task.

## Notes

- Update BUG-T9 status and resolution checklist in `SPECS/Workplan.md` after implementation.
- If behavior changes meaningfully for operators, add a short troubleshooting note about automatic stale-process cleanup.
