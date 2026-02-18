# PRD: FU-P13-T2-2 — Move PID file write to after successful upstream launch

**Task ID:** FU-P13-T2-2  
**Priority:** P3  
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session  
**Dependencies:** P13-T2  
**Status:** Planned

## Objective

Eliminate a startup race in `BrokerDaemon.start()` where the PID file can be written before
`_launch_upstream()` succeeds. If startup fails between these operations, the wrapper can leave a
live-process PID lock that blocks future starts. The fix is to move PID-file persistence so it
runs only after upstream launch has completed successfully.

## Success Criteria

- PID file is created only after `_launch_upstream()` succeeds.
- Failure paths during upstream launch do not leave a PID file behind.
- Existing stale-lock behavior and cleanup flows remain unchanged.
- Current broker daemon tests remain green, and coverage for this behavior is explicit.

## Acceptance Tests

1. Existing test coverage for successful startup still passes.
2. Existing test coverage for startup failures still passes.
3. Add or update a unit test that proves no PID file is written when `_launch_upstream()` raises.
4. Verify lock/PID cleanup behavior remains correct after stop or failed start.

## Test-First Plan

1. Inspect `tests/unit/test_broker_daemon.py` around startup/lifecycle tests and identify current
   assertions for PID file timing.
2. Add/adjust a failing test asserting PID file write happens after successful upstream launch and
   does not happen on launch failure.
3. Run focused tests for broker daemon to confirm the new test fails before implementation.

## Implementation Plan

### Phase 1: Validate current startup order
- **Inputs:** `src/mcpbridge_wrapper/broker/daemon.py`, existing broker daemon tests.
- **Outputs:** Confirmed execution order and concrete edit target in `start()`.
- **Verification:** Readable call order documented in PR notes.

### Phase 2: Move PID write after upstream launch
- **Inputs:** `BrokerDaemon.start()`.
- **Outputs:** Refactored startup sequence with unchanged external behavior.
- **Verification:** New/updated test passes and no regressions in daemon lifecycle tests.

### Phase 3: Run required quality gates + report
- **Inputs:** Updated source and tests.
- **Outputs:** Passing `pytest`, `ruff check src/`, `mypy src/`, and `pytest --cov` results plus
  `SPECS/INPROGRESS/FU-P13-T2-2_Validation_Report.md`.
- **Verification:** Command outputs captured with PASS/FAIL summary and coverage percentage.

## Risks and Mitigations

- **Risk:** Changing startup ordering could break assumptions in lock handling.
  **Mitigation:** Keep lock acquisition timing unchanged and rely on existing stale-lock tests.
- **Risk:** Test fixtures may mock PID writes loosely.
  **Mitigation:** Add explicit assertions around PID path existence and write invocation order.

## Notes

- If behavior changes are not user-visible, no documentation updates are required.
- If startup semantics or troubleshooting guidance changes, update `docs/troubleshooting.md`.
