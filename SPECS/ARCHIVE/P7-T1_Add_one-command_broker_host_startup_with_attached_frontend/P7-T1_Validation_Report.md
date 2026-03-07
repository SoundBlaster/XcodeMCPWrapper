# P7-T1 Validation Report

**Task:** P7-T1 — Add one-command broker host startup with attached frontend
**Date:** 2026-03-07
**Verdict:** PASS

## Summary

Implemented a one-command broker console startup flow by:

- adding `--broker-console` as an explicit orchestration mode in
  `src/mcpbridge_wrapper/__main__.py`
- reusing the existing dedicated broker host topology instead of introducing a
  new broker lifecycle model
- validating that the target dashboard is actually broker-backed before opening
  the TUI
- refusing to launch into a broken session when a stale broker is already
  running or when the dashboard port is occupied by a foreign listener
- spawning the dedicated host detached from the terminal while routing daemon
  logs into `~/.mcpbridge_wrapper/broker.log` for operator diagnostics
- extending terminal frontend plumbing with a reusable backend probe in
  `src/mcpbridge_wrapper/tui.py`
- adding focused unit coverage for CLI validation, helper orchestration,
  backend readiness, timeout/error messaging, and detached host spawn wiring

## Files Validated

- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/tui.py`
- `tests/unit/test_main.py`
- `tests/unit/test_main_tui.py`
- `tests/unit/test_tui.py`

## Targeted Verification

```bash
pytest tests/unit/test_main_tui.py
```

- Result: `14 passed`

```bash
pytest tests/unit/test_tui.py
```

- Result: `34 passed`

```bash
pytest tests/unit/test_main.py -k 'broker_console or read_running_broker_pid or recent_broker_events_hint'
```

- Result: `19 passed`

```bash
ruff check tests/unit/test_main.py tests/unit/test_main_tui.py
```

- Result: `All checks passed!`

## Required Quality Gates

```bash
pytest
```

- Result: `854 passed, 5 skipped in 8.08s`

```bash
ruff check src/ tests/
```

- Result: `All checks passed!`

```bash
mypy src/
```

- Result: `Success: no issues found in 19 source files`

```bash
pytest --cov=src --cov-report=term
```

- Result: `854 passed, 5 skipped in 9.01s`
- Coverage: `91.72%`

## Notes

- The new flow keeps `--tui` attach-only; lifecycle management is isolated to
  `--broker-console`.
- Coverage remains above the repository threshold of `90%` after adding the new
  orchestration paths.
- Remaining warnings are pre-existing dependency deprecations from
  `websockets` / `uvicorn`, not regressions introduced by this task.
