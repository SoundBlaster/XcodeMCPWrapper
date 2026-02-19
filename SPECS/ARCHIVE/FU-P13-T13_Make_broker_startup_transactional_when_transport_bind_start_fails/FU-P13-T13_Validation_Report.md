# Validation Report: FU-P13-T13 — Make broker startup transactional when transport bind/start fails

**Date:** 2026-02-19
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | If `transport.start()` raises, upstream subprocess is terminated and fully waited | ✅ PASS |
| 2 | If `transport.start()` raises, PID and socket files are removed | ✅ PASS |
| 3 | Broker state is `STOPPED` after any rollback | ✅ PASS |
| 4 | The original exception from `transport.start()` propagates out of `BrokerDaemon.start()` | ✅ PASS |
| 5 | If `pid_file.write_text()` raises, upstream is also rolled back | ✅ PASS |
| 6 | Unit tests cover all rollback scenarios | ✅ PASS |
| 7 | Quality gates: `pytest`, `ruff check src/`, `mypy src/` all pass | ✅ PASS |

---

## Test Results

```
PYTHONPATH=.../src:.../site-packages pytest tests/ --ignore=tests/integration -q
559 passed, 10 skipped in 8.99s
```

New tests in `TestStartupRollback` (6 tests added):

| Test | Result |
|------|--------|
| `test_transport_start_failure_terminates_upstream` | PASS |
| `test_transport_start_failure_removes_pid_file` | PASS |
| `test_transport_start_failure_removes_socket_file` | PASS |
| `test_transport_start_failure_state_is_stopped` | PASS |
| `test_transport_start_failure_reraises_exception` | PASS |
| `test_pid_write_failure_terminates_upstream` | PASS |

---

## Quality Gates

| Gate | Result |
|------|--------|
| `ruff check src/` | ✅ All checks passed |
| `ruff check tests/` | ✅ All checks passed |
| `mypy src/` | ✅ 3 pre-existing errors only (unrelated files) |
| `pytest tests/ --ignore=tests/integration` | ✅ 559 passed, 10 skipped |

---

## Files Changed

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Restructured `start()` with try/except rollback; added `_rollback_startup()` |
| `tests/unit/test_broker_daemon.py` | Added `TestStartupRollback` class (6 tests) |
| `docs/troubleshooting.md` | Added broker startup bind-error section |

---

## Summary

The `BrokerDaemon.start()` method is now fully transactional. All steps after
`_launch_upstream()` are wrapped in a try/except block that calls `_rollback_startup()`
on any exception. The rollback cancels the read task, terminates the upstream subprocess,
removes PID/socket files, and sets state to `STOPPED`. The original exception is always
re-raised. `self._state = BrokerState.READY` is only set after all startup steps succeed.
