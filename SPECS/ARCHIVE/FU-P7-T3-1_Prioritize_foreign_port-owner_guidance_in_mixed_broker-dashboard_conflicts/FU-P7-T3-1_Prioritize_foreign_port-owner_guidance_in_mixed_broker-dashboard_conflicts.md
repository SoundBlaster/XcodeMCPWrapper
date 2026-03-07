# FU-P7-T3-1 — Prioritize foreign port-owner guidance in mixed broker/dashboard conflicts

## Objective Summary

`P7-T3` removed the silent “broker alive, dashboard absent” partial state, but
its review found one remaining mixed-state failure mode: when a broker PID is
still live and the requested dashboard port is simultaneously occupied by a
foreign listener, startup guidance prioritizes the broker reset path and can
hide the actual port owner. That can send users into a reset loop while the
real blocker, the unrelated listener on the port, remains untouched.

This follow-up should make mixed-state diagnostics explicit across both startup
and `--doctor`. The goal is not to invent a new recovery workflow. Instead,
the code should surface the foreign port owner first or name both blockers in
one clear remediation path, while preserving the existing single-listener and
broker-without-dashboard behavior for non-mixed states.

## Deliverables

- Update `src/mcpbridge_wrapper/__main__.py` so mixed-state startup failures
  can report both a live broker PID and a foreign dashboard-port listener
  instead of hiding the listener behind broker-reset guidance.
- Update `src/mcpbridge_wrapper/doctor.py` so mixed broker/listener conflicts
  classify as a port-ownership issue rather than the generic
  `broker-without-dashboard` diagnosis.
- Add regression coverage in `tests/unit/test_main.py` and
  `tests/unit/test_doctor.py` for the mixed-state conflict path.
- Produce `SPECS/INPROGRESS/FU-P7-T3-1_Validation_Report.md` with required
  quality-gate evidence.

## Success Criteria

- `--broker-console` and `--broker-daemon --web-ui` mention the foreign
  dashboard-port listener or both blockers when a live broker PID and foreign
  listener coexist.
- `--doctor` no longer hides the foreign listener behind a generic
  broker-without-dashboard diagnosis in the same mixed state.
- Regression tests pin the mixed-state ordering so future changes cannot revert
  to broker-only guidance.

## Test-First Plan

1. Add startup tests that model the mixed state for both `_run_broker_console()`
   and `main()`’s `--broker-daemon --web-ui` path, asserting the foreign port
   owner is surfaced alongside the live broker PID.
2. Add a doctor-classification test for a live local broker plus foreign
   listener on the configured dashboard port, asserting the report stays in the
   port-occupied family instead of `broker-without-dashboard`.
3. Implement the smallest production changes needed to collect both blockers
   before choosing the user-facing guidance path.
4. Run the required quality gates: `pytest`, `ruff check src/`, `mypy src/`,
   and `pytest --cov`.

## Execution Plan

### Phase 1: Pin the mixed-state startup contract

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- existing `P7-T3` startup tests in `tests/unit/test_main.py`

Outputs:
- regression tests for mixed-state broker PID + foreign listener conflicts
- a precise expected stderr contract for broker-console and broker-daemon flows

Verification:
- the new startup tests fail on the current ordering that hides the foreign
  listener

### Phase 2: Align startup guidance

Inputs:
- `_run_broker_console()`
- `_report_requested_dashboard_unavailable()`
- broker-daemon web-ui startup branch in `main()`

Outputs:
- startup logic that can see both `running_broker_pid` and `listener_pids`
- one explicit remediation path that surfaces the foreign listener without
  dropping broker-state context

Verification:
- startup messaging for single-blocker states remains unchanged
- mixed-state messaging mentions the foreign listener or both blockers

### Phase 3: Align doctor classification and validate

Inputs:
- `src/mcpbridge_wrapper/doctor.py`
- doctor classification tests
- full repo quality gates

Outputs:
- mixed-state doctor report that stays actionable and consistent with startup
- validation report with targeted and full quality-gate evidence

Verification:
- `--doctor` and startup both direct the user toward resolving the foreign port
  conflict before or alongside broker reset
- coverage remains at or above the repository threshold

## Acceptance Tests

- `pytest tests/unit/test_main.py`
- `pytest tests/unit/test_doctor.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer a combined-message approach when both blockers are real; users should
  not lose visibility into the live broker PID just because the foreign
  listener is now prioritized.
- Keep the public recovery commands aligned with `P7-T3` and `P7-T2` rather
  than inventing a new remediation surface for this follow-up.

## Notes

- No documentation changes are expected unless the implementation forces
  observable command/help text changes beyond stderr diagnostics.
- Review subject name for this task: `mixed_dashboard_conflict_guidance`.

---
**Archived:** 2026-03-07
**Verdict:** PASS
