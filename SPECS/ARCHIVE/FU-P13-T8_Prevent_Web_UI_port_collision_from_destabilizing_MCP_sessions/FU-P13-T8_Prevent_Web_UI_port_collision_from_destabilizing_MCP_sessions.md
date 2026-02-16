# FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions

**Status:** In Progress
**Branch:** feature/FU-P13-T8-web-ui-port-collision
**Priority:** P0
**Phase:** 13 (Follow-up)

---

## Problem Statement

When the `--web-ui` port is occupied (e.g. by a stale/orphan wrapper process from a previous Cursor restart), the current code's `is_port_available()` check prevents starting a duplicate listener. However, there is a **TOCTOU window**: the check may pass, the daemon thread starts, and then uvicorn fails to bind — raising `SystemExit(1)` inside the daemon thread. Since `run_server()` only catches `OSError`, the `SystemExit` propagates as an unhandled thread exception, producing a pytest warning during tests and, in production, leaking a daemon thread exception to stderr noise.

The troubleshooting documentation for stale-process cleanup was already added in `FU-BUG-T6-1` and is present in `docs/troubleshooting.md`.

---

## Current State Analysis

### What already works
- `is_port_available()` pre-check in `__main__.py` (lines 274–285): if the port is occupied at check time, a `Warning:` is printed to stderr and Web UI is skipped; MCP bridge starts normally.
- `--web-ui-only` returns exit code 1 with a clear error message when port is occupied.
- `run_server()` already catches `OSError` from uvicorn.
- `TestPortCollisionHandling` class covers: occupied-port bridge mode, occupied-port `--web-ui-only` mode, free-port normal start, and `is_port_available` socket-level tests.
- Troubleshooting docs in `docs/troubleshooting.md` cover stale-process cleanup.

### Gap: `SystemExit` not caught in `run_server()`
Uvicorn internally catches the `OSError` from port binding and calls `sys.exit(1)`, raising `SystemExit(1)`. The `run_server()` wrapper only catches `OSError`, so `SystemExit` propagates as an unhandled daemon-thread exception. This is visible as:
- `PytestUnhandledThreadExceptionWarning` in test output when real port 8080 is occupied
- Daemon thread stderr noise in production if TOCTOU window is hit

---

## Deliverables

1. **`src/mcpbridge_wrapper/webui/server.py`** — Extend the `except OSError` in `run_server()` to also catch `SystemExit`, with an appropriate stderr message.

2. **`tests/unit/test_main_webui.py`** — Add a test in `TestPortCollisionHandling` for the TOCTOU scenario: `is_port_available` returns `True` but uvicorn fails to bind (simulated by raising `SystemExit(1)` from `uvicorn.run`), verifying the thread does NOT produce an unhandled exception.

3. **`SPECS/Workplan.md`** — Mark FU-P13-T8 acceptance criteria as satisfied.

---

## Acceptance Criteria

- [x] When requested Web UI port is occupied, wrapper behavior is explicit and deterministic (clear error or safe fallback) — handled by `is_port_available` pre-check (already done in BUG-T6)
- [x] MCP stdio protocol output remains valid JSON-RPC only on stdout — maintained; port check and warning go to stderr only
- [x] Repeated client startups no longer accumulate conflicting Web UI listeners on the same port — `is_port_available` prevents duplicate server starts
- [ ] `run_server()` catches `SystemExit` from uvicorn's `sys.exit(1)` on bind failure — **this task's code fix**
- [ ] No unhandled thread exceptions from Web UI daemon thread on port collision — verified by new TOCTOU test
- [ ] Tests cover occupied-port and restart scenarios — existing + new TOCTOU test

---

## Implementation Plan

### 1. Fix `run_server()` — catch `SystemExit`

In `src/mcpbridge_wrapper/webui/server.py`, extend the `except OSError` block:

```python
try:
    uvicorn.run(...)
except OSError as exc:
    print(f"Warning: Web UI server could not bind to {host}:{port}: {exc}", file=sys.stderr)
except SystemExit:
    # uvicorn calls sys.exit(1) when port binding fails; treat as bind error
    print(
        f"Warning: Web UI server failed to start on {server_config.host}:{server_config.port}. "
        "Port may have become occupied after the availability check.",
        file=sys.stderr,
    )
```

### 2. Add TOCTOU regression test

In `tests/unit/test_main_webui.py`, add to `TestPortCollisionHandling`:

```python
def test_toctou_port_occupied_after_check_does_not_crash_thread(self):
    """If port is free at check time but uvicorn fails to bind (TOCTOU),
    the daemon thread exits cleanly without an unhandled exception."""
```

Simulate by patching `uvicorn.run` to raise `SystemExit(1)` and verifying no exception is raised from `run_server`.

### 3. Update workplan

Mark `FU-P13-T8` acceptance criteria as completed in `SPECS/Workplan.md`.

---

## Dependencies

- P10-T1 ✅ (Web UI foundation)
- BUG-T6 ✅ (initial port collision handling)
- FU-BUG-T6-1 ✅ (stale-process troubleshooting docs)

---

## Quality Gates

- `pytest tests/unit/test_main_webui.py` — all pass, no thread exception warnings
- `ruff check src/` — no lint errors
- `pytest --cov` — coverage ≥ 90%
