# FU-P7-T3-1 Validation Report

**Task:** FU-P7-T3-1 — Prioritize foreign port-owner guidance in mixed broker/dashboard conflicts
**Date:** 2026-03-07
**Verdict:** PASS

## Summary

Implemented the `FU-P7-T3-1` follow-up by:

- updating startup guidance in `src/mcpbridge_wrapper/__main__.py` so mixed
  broker/dashboard conflicts can surface both a live broker PID and a foreign
  listener on the requested dashboard port
- fixing `_run_broker_console()` so it inspects the configured dashboard port
  before returning early on a running broker PID, allowing mixed-state
  reporting instead of broker-only guidance
- aligning `src/mcpbridge_wrapper/doctor.py` so mixed broker-plus-listener
  states classify as a port-ownership issue rather than being hidden behind the
  generic `broker-without-dashboard` diagnosis
- adding regression coverage for broker-console, broker-daemon `--web-ui`, and
  doctor mixed-state flows

## Files Validated

- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/doctor.py`
- `tests/unit/test_main.py`
- `tests/unit/test_doctor.py`

## Targeted Verification

```bash
pytest tests/unit/test_main.py tests/unit/test_doctor.py -k 'mixed_state_mentions_foreign_listener or mixed_broker_and_foreign_listener_prefers_port_conflict'
```

- Result: `3 passed`
- Observed outcome: startup and doctor now keep the foreign port owner visible
  in mixed broker/listener conflicts

```bash
pytest tests/unit/test_main.py tests/unit/test_doctor.py
```

- Result: `119 passed`

## Required Quality Gates

```bash
pytest
```

- Result: `891 passed, 5 skipped in 8.14s`

```bash
ruff check src/
```

- Result: `All checks passed!`

```bash
mypy src/
```

- Result: `Success: no issues found in 20 source files`

```bash
pytest --cov
```

- Result: `891 passed, 5 skipped in 9.16s`
- Coverage: `91.64%`

## Acceptance Criteria Evidence

- [x] `--broker-console` and `--broker-daemon --web-ui` surface the foreign
  dashboard-port owner or both blockers when a live broker PID and foreign
  listener coexist.
  - Evidence: `tests/unit/test_main.py::TestBrokerConsoleHelpers::test_run_broker_console_mixed_state_mentions_foreign_listener`
    and
    `tests/unit/test_main.py::TestMainBrokerWebUIFlowCoverage::test_main_broker_daemon_webui_mixed_state_mentions_foreign_listener`
    both passed.
- [x] `--doctor` does not hide the foreign listener behind a generic
  broker-without-dashboard diagnosis in the same mixed state.
  - Evidence:
    `tests/unit/test_doctor.py::TestClassifyDoctorReport::test_classify_mixed_broker_and_foreign_listener_prefers_port_conflict`
    passed with `report.code == "port-occupied"`.
- [x] Regression tests cover the mixed-state conflict and prevent reordering
  back to broker-only guidance.
  - Evidence: new mixed-state tests were added in `tests/unit/test_main.py` and
    `tests/unit/test_doctor.py`, and the targeted plus full affected-module
    suites passed.

## Notes

- The mixed-state fix keeps existing single-blocker behavior unchanged: plain
  broker-without-dashboard and plain foreign-listener paths still use their
  original guidance.
- Existing `websockets` / `uvicorn` deprecation warnings remain in the suite
  and are unrelated to this task.
