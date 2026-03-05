# Validation Report — P4-T1

**Task:** P4-T1 — Auto-restart stale broker daemon on version mismatch after upgrade  
**Date:** 2026-03-05  
**Executor:** Codex (`flow-run`)  
**Verdict:** PASS

## Summary

Implemented and validated version-aware broker lifecycle handling across runtime code, CLI, scripts, documentation, and tests.

Key outcomes:
- `__version__` now resolves from package metadata with safe fallback.
- Broker daemon writes/cleans `broker.version` and reports version in status payload.
- Proxy detects daemon version mismatch and restarts stale daemon before reuse.
- Added `--broker-status` and `--broker-stop` commands.
- Install/uninstall scripts now stop running broker daemons before file operations.
- Broker mode docs updated for new status/stop/version management workflow.
- Coverage restored above threshold after adding targeted tests for new paths.

## Acceptance Criteria Check

- [x] `__version__` derived from `importlib.metadata` (single source: `pyproject.toml`)
- [x] Daemon writes `~/.mcpbridge_wrapper/broker.version` on start and cleans on stop
- [x] Proxy auto-restarts daemon when version file mismatches current `__version__`
- [x] No version file (old daemon) treated as compatible
- [x] `--broker-status` prints daemon PID, version, mismatch warning
- [x] `--broker-stop` sends SIGTERM, waits, and cleans up state files
- [x] `scripts/install.sh` stops running broker daemon before writing new wrapper
- [x] `scripts/uninstall.sh` stops running broker daemon before removing files
- [x] `docs/broker-mode.md` documents `--broker-stop`, `--broker-status`, and version management
- [x] All quality gates pass (`pytest`, `ruff`, `mypy`, coverage >= 90%)

## Quality Gate Evidence

```bash
pytest
```

Result: `766 passed, 5 skipped, 2 warnings`.

```bash
ruff check src/
```

Result: `All checks passed!`.

```bash
mypy src/mcpbridge_wrapper
```

Result: `Success: no issues found in 18 source files`.

```bash
pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing
```

Result: `766 passed, 5 skipped, 2 warnings`; total coverage `90.71%` (threshold `90%`).

## Additional Test Coverage Added

- `tests/unit/test_main.py`:
  - New coverage for `--broker-status` and `--broker-stop` runtime branches.
- `tests/unit/test_broker_proxy.py`:
  - New coverage for version-file read errors and `_stop_stale_daemon` cleanup paths.
- `tests/unit/test_init.py`:
  - Metadata-derived version and fallback behavior.

## Notes

- Existing deprecation warnings from websocket dependencies remain unchanged and are non-blocking for this task.
- Ready for ARCHIVE step.
