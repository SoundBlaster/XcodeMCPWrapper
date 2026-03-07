# FU-P7-T3-2 Validation Report

**Task:** FU-P7-T3-2 — Exclude broker-owned dashboard listeners from foreign port-conflict guidance
**Date:** 2026-03-07
**Verdict:** PASS

## Summary

Implemented the `FU-P7-T3-2` follow-up by:

- updating `src/mcpbridge_wrapper/__main__.py` so mixed-state startup guidance
  filters out the running broker PID before treating dashboard listeners as a
  foreign port conflict
- updating `src/mcpbridge_wrapper/doctor.py` so doctor classification applies
  the same ownership filter before returning `port-occupied`
- extending startup and doctor regressions so foreign-listener cases still
  trigger occupied-port guidance, while broker-owned-listener cases stay on the
  broker-health reset path

## Files Validated

- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/doctor.py`
- `tests/unit/test_main.py`
- `tests/unit/test_doctor.py`

## Targeted Verification

```bash
pytest tests/unit/test_main.py tests/unit/test_doctor.py -k 'same_pid_listener or broker_owned_listener or mixed_broker_and_foreign_listener_prefers_port_conflict or mixed_state_mentions_foreign_listener'
```

- Result: `6 passed`
- Observed outcome: foreign-listener mixed states still surface occupied-port
  guidance, while same-PID listener states stay on broker-health guidance.

```bash
pytest tests/unit/test_main.py tests/unit/test_doctor.py
```

- Result: `122 passed`

## Required Quality Gates

```bash
pytest
```

- Result: `894 passed, 5 skipped in 7.95s`

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

- Result: `894 passed, 5 skipped in 8.75s`
- Coverage: `91.78%`

## Acceptance Criteria Evidence

- [x] `--broker-console` and `--broker-daemon --web-ui` only surface
  foreign-listener occupied-port guidance when `listener_pids` contains at
  least one PID other than the running broker PID.
  - Evidence:
    `tests/unit/test_main.py::TestBrokerConsoleHelpers::test_run_broker_console_mixed_state_mentions_foreign_listener`,
    `tests/unit/test_main.py::TestBrokerConsoleHelpers::test_run_broker_console_same_pid_listener_uses_broker_reset_guidance`,
    `tests/unit/test_main.py::TestMainBrokerWebUIFlowCoverage::test_main_broker_daemon_webui_mixed_state_mentions_foreign_listener`,
    and
    `tests/unit/test_main.py::TestMainBrokerWebUIFlowCoverage::test_main_broker_daemon_webui_same_pid_listener_uses_broker_reset_guidance`
    all passed.
- [x] `--doctor` does not classify a broker-owned dashboard listener plus
  degraded probes as "stop the existing listener"; it stays on broker-health
  guidance.
  - Evidence:
    `tests/unit/test_doctor.py::TestClassifyDoctorReport::test_classify_broker_owned_listener_uses_broker_without_dashboard`
    passed with `report.code == "broker-without-dashboard"`, while
    `test_classify_mixed_broker_and_foreign_listener_prefers_port_conflict`
    still passed with `report.code == "port-occupied"`.
- [x] Regression tests cover both the foreign-listener and broker-owned-listener
  mixed states so future refactors cannot reintroduce self-conflict messaging.
  - Evidence: `tests/unit/test_main.py` and `tests/unit/test_doctor.py` now
    cover mixed sets containing both the broker PID and a foreign PID, plus the
    same-PID-only path.

## Notes

- Existing `websockets` / `uvicorn` deprecation warnings remain in the suite
  and are unrelated to this task.
