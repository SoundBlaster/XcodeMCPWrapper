# FU-P7-T1-1 — Normalize KeyboardInterrupt handling when broker-console reuses an existing host

## Objective Summary

`P7-T1` introduced `--broker-console` as the recommended one-command entrypoint
for the dedicated broker host plus attached TUI. The spawned-host path already
wraps `run_tui(runtime)` in a `try/except KeyboardInterrupt` block and returns
exit code `0`, matching standalone `--tui` behavior. The reuse-existing-host
path does not: when `_probe_broker_console_backend(runtime)` reports a healthy
broker-backed dashboard, `_run_broker_console()` returns `run_tui(runtime)`
directly and lets `Ctrl-C` bubble out differently.

This follow-up should remove that inconsistency without widening scope. The
fix should make `--broker-console` behave the same whether it reuses an already
healthy dashboard or spawns a new host, and it should pin that contract with a
dedicated regression test.

## Deliverables

- Update `src/mcpbridge_wrapper/__main__.py` so `_run_broker_console()` handles
  `KeyboardInterrupt` consistently across both the ready-backend reuse path and
  the spawn-then-attach path.
- Extend `tests/unit/test_main.py` (or the most targeted CLI/TUI test module)
  with regression coverage for `run_tui()` raising `KeyboardInterrupt` while
  `--broker-console` is reusing an existing healthy backend.
- Produce `SPECS/INPROGRESS/FU-P7-T1-1_Validation_Report.md` with required
  quality-gate evidence and acceptance checks.

## Success Criteria

- `--broker-console` returns exit code `0` when users press `Ctrl-C` after the
  command attaches to an already healthy broker-backed dashboard.
- The behavior matches the existing spawned-host `--broker-console` path and
  standalone `--tui` mode.
- Regression tests fail before the fix and pass after it.

## Test-First Plan

1. Add a unit test that sets `_probe_broker_console_backend()` to ready,
   patches `run_tui()` to raise `KeyboardInterrupt`, and asserts
   `_run_broker_console()` returns `0`.
2. Confirm the existing spawned-host interrupt test still covers the deferred
   path where `_wait_for_broker_console_backend()` succeeds after spawn.
3. Implement the smallest code change needed in `_run_broker_console()`.
4. Run the required quality gates: `pytest`, `ruff check src/`, `mypy src/`,
   and `pytest --cov`.

## Execution Plan

### Phase 1: Pin the reuse-path contract

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- `tests/unit/test_main.py`

Outputs:
- one focused regression test for the ready-backend reuse path
- verified understanding of current interrupt handling across `--tui` and
  `--broker-console`

Verification:
- the new test reproduces the inconsistency on the current implementation

### Phase 2: Normalize the implementation

Inputs:
- `_run_broker_console()` reuse and spawn branches
- existing `KeyboardInterrupt` handling in `main()` and `_run_broker_console()`

Outputs:
- a single interrupt-handling path for both attach modes
- no behavior changes to error/reporting branches unrelated to `Ctrl-C`

Verification:
- both reuse and spawn paths return `0` on `KeyboardInterrupt`

### Phase 3: Validate and document completion

Inputs:
- updated implementation and unit tests
- repo quality gates

Outputs:
- `FU-P7-T1-1_Validation_Report.md`
- pass/fail evidence for task acceptance criteria

Verification:
- targeted tests and full project quality gates remain green

## Acceptance Tests

- `pytest tests/unit/test_main.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer the narrowest fix in `_run_broker_console()` instead of introducing a
  broader TUI wrapper abstraction unless the code clearly benefits from it.
- Keep exit-code normalization local to command entrypoints; the TUI itself
  should not need to know whether it was launched in reuse or spawn mode.

## Notes

- No documentation changes are expected for this follow-up because the user
  facing command shape stays the same.
- Review subject name for this task: `broker_console_keyboardinterrupt_reuse`.

---
**Archived:** 2026-03-07
**Verdict:** PASS
