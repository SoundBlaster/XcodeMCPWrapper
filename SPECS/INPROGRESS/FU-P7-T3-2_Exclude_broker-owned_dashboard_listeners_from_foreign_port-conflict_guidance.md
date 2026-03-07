# FU-P7-T3-2 — Exclude broker-owned dashboard listeners from foreign port-conflict guidance

## Objective Summary

`FU-P7-T3-1` fixed the case where a live broker PID and a foreign process on
the requested dashboard port were collapsed into broker-only remediation.
Review of that change found one remaining ownership gap: the mixed-state branch
currently treats any listener on the dashboard port as foreign, even when the
listener belongs to the same broker daemon named by the PID file. When backend
probes degrade while the broker still owns the port, startup and `--doctor`
can incorrectly tell users to stop an "existing listener" or use
`--web-ui-restart`, even though the right guidance is still the broker-health
path.

This follow-up should keep the mixed-state foreign-listener behavior from
`FU-P7-T3-1`, but make it ownership-aware. The implementation should filter out
the broker daemon PID before choosing the foreign-listener/port-occupied path,
while leaving single-blocker behavior unchanged for genuine foreign listeners
and broker-without-dashboard states.

## Deliverables

- Update `src/mcpbridge_wrapper/__main__.py` so mixed-state startup guidance
  only treats listener PIDs that differ from the running broker PID as foreign
  port conflicts.
- Update `src/mcpbridge_wrapper/doctor.py` so mixed-state diagnostics use the
  same broker-owned-listener exclusion before returning `port-occupied`.
- Extend `tests/unit/test_main.py` and `tests/unit/test_doctor.py` with
  broker-owned-listener regression coverage alongside the existing
  foreign-listener tests.
- Produce `SPECS/INPROGRESS/FU-P7-T3-2_Validation_Report.md` with targeted and
  full quality-gate results.

## Success Criteria

- `--broker-console` and `--broker-daemon --web-ui` only surface
  foreign-listener occupied-port guidance when `listener_pids` contains at
  least one PID other than the running broker PID.
- `--doctor` does not classify a broker-owned dashboard listener plus degraded
  probes as "stop the existing listener"; it stays on broker-health guidance.
- Regression tests cover both the foreign-listener and broker-owned-listener
  mixed states so future refactors cannot reintroduce self-conflict messaging.

## Test-First Plan

1. Extend the existing startup tests for `_run_broker_console()` and
   `main()`’s `--broker-daemon --web-ui` flow with a same-PID listener case,
   asserting the error stays on the broker-reset/broker-health path and does
   not mention "existing listener" or `--web-ui-restart`.
2. Extend the mixed-state doctor classification coverage with a dashboard
   listener list that contains the local broker PID, asserting the report stays
   in the `broker-without-dashboard` family instead of `port-occupied`.
3. Implement the smallest production change needed to derive a foreign-listener
   subset before selecting user-facing remediation.
4. Run `pytest`, `ruff check src/`, `mypy src/`, and `pytest --cov`.

## Execution Plan

### Phase 1: Pin the self-listener contract

Inputs:
- `tests/unit/test_main.py`
- `tests/unit/test_doctor.py`
- existing foreign-listener regressions from `FU-P7-T3-1`

Outputs:
- failing tests for broker-owned listener mixed states in startup and doctor

Verification:
- the new tests fail against the current branch because self-owned listeners
  still route through foreign-listener guidance

### Phase 2: Filter broker-owned listener PIDs

Inputs:
- `_report_requested_dashboard_unavailable()` and `_run_broker_console()` in
  `src/mcpbridge_wrapper/__main__.py`
- `classify_doctor_report()` in `src/mcpbridge_wrapper/doctor.py`

Outputs:
- a minimal ownership-aware listener filter shared by startup and doctor logic
- unchanged messaging for genuine foreign listeners and plain
  broker-without-dashboard states

Verification:
- mixed-state occupied-port guidance only appears when a non-broker PID still
  owns the dashboard port

### Phase 3: Validate and archive

Inputs:
- updated production code
- targeted and full test suites

Outputs:
- passing targeted regressions and full quality gates
- validation report ready for ARCHIVE

Verification:
- coverage remains at or above the repository threshold
- review can focus on ownership precision rather than broad behavior changes

## Acceptance Tests

- `pytest tests/unit/test_main.py`
- `pytest tests/unit/test_doctor.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer filtering the listener PID set over rewriting the message hierarchy;
  the user-visible behavior from `FU-P7-T3-1` should remain intact for genuine
  foreign listeners.
- If multiple listener PIDs are present and one matches the broker PID, the
  code should still report a port conflict when any remaining PID is foreign.

## Notes

- No documentation updates are expected unless stderr wording changes beyond
  the existing broker-health and foreign-listener guidance surfaces.
- Review subject name for this task: `broker_owned_listener_guidance`.
