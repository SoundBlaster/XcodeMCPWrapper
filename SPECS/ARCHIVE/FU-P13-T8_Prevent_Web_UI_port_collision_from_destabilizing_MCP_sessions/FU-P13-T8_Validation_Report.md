# FU-P13-T8 Validation Report

**Task:** Prevent Web UI port collision from destabilizing MCP sessions
**Date:** 2026-02-16
**Branch:** feature/FU-P13-T8-web-ui-port-collision

---

## Summary

**PASS** — All acceptance criteria met. Code fix is minimal and targeted (1 new `except` clause). All quality gates pass with improved test coverage.

---

## Changes Made

### `src/mcpbridge_wrapper/webui/server.py`
- Extended `run_server()` to catch `SystemExit` in addition to `OSError`
- Uvicorn internally calls `sys.exit(1)` when port binding fails, which was propagating as an unhandled daemon-thread exception (visible as `PytestUnhandledThreadExceptionWarning`)
- New `except SystemExit` block prints a clear warning to stderr and allows the thread to exit cleanly

### `tests/unit/test_main_webui.py`
- Added `test_toctou_systemexit_from_uvicorn_does_not_crash_thread` to `TestPortCollisionHandling`
- Verifies that when `uvicorn.run()` raises `SystemExit(1)` (TOCTOU scenario), `run_server()` catches it without propagating an unhandled exception
- Verifies the warning message is printed to stderr

### `SPECS/Workplan.md`
- Marked FU-P13-T8 acceptance criteria as `[x]` satisfied
- Added `✅` status marker and implementation date

---

## Quality Gates

| Gate | Command | Result |
|------|---------|--------|
| Unit tests | `pytest tests/` | ✅ 472 passed, 5 skipped |
| Lint | `ruff check src/` | ✅ All checks passed |
| Coverage | `pytest --cov` | ✅ 95.6% (≥90% required) |

### Test File Coverage Before vs After

| Test file | Before | After |
|-----------|--------|-------|
| `test_main_webui.py` | 41 tests, 1 PytestUnhandledThreadExceptionWarning | 42 tests, 0 warnings |

---

## Acceptance Criteria

- [x] When requested Web UI port is occupied, wrapper behavior is explicit and deterministic — handled by `is_port_available()` pre-check (BUG-T6) + new `SystemExit` catch for TOCTOU
- [x] MCP stdio protocol output remains valid JSON-RPC only on stdout — warnings go to stderr only
- [x] Repeated client startups no longer accumulate conflicting Web UI listeners — `is_port_available()` prevents duplicate binds; TOCTOU window covered by `SystemExit` catch
- [x] Tests cover occupied-port and restart scenarios — existing `TestPortCollisionHandling` class + new TOCTOU test

---

## Pre-existing State Verified

- `is_port_available()` pre-check already in `__main__.py` (from BUG-T6)
- Troubleshooting docs for stale-process cleanup already in `docs/troubleshooting.md` (from FU-BUG-T6-1)
- `TestPortCollisionHandling` test class already present (from BUG-T6)

The only gap was the unhandled `SystemExit` from uvicorn in the TOCTOU case — now addressed.
