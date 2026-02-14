# BUG-T6: Web UI Port Collisions Create Unstable Multi-Process Behavior

**Task ID:** BUG-T6
**Type:** Bug / Runtime / Process Lifecycle
**Priority:** P0
**Status:** In Progress
**Implements:** FU-P13-T8
**Date:** 2026-02-14

---

## 1. Problem Statement

When multiple stale/orphan wrapper instances exist (e.g., after a client restarts), they all
attempt to bind to the same Web UI port (default `8080`). The result is a flood of bind errors
logged to stderr that:
1. Clutter the stderr channel used for diagnostic messages
2. Prevent new instances from starting a usable Web UI
3. Create an undefined mix of stale and new listeners on the same host:port

The core issue is that `run_server` / `run_server_in_thread` do not check port availability
before starting, and the caller (`__main__.py`) does not handle the `OSError` that results.

---

## 2. Deliverables

| # | Artifact | Path |
|---|----------|------|
| 1 | Port-check utility function | `src/mcpbridge_wrapper/webui/server.py` |
| 2 | Collision handling in `__main__.py` startup | `src/mcpbridge_wrapper/__main__.py` |
| 3 | Unit tests for collision scenarios | `tests/unit/test_main_webui.py` |
| 4 | Validation report | `SPECS/INPROGRESS/BUG-T6_Validation_Report.md` |

---

## 3. Design

### 3.1 Port availability check

Add a helper `is_port_available(host, port) -> bool` in `server.py` that attempts a
`socket.bind()` and returns `False` if `OSError` is raised (i.e., port occupied).

### 3.2 Startup collision handling in `__main__.py`

Before calling `run_server_in_thread` (or `run_server` in `--web-ui-only` mode):
1. Call `is_port_available(config.host, config.port)`.
2. If the port is **occupied**:
   - Print a clear message to stderr:
     `Warning: Web UI port {port} is already in use. Skipping Web UI startup.`
   - Continue WITHOUT starting the Web UI thread (MCP stdio bridge still starts normally).
   - Do NOT exit with an error — the MCP session must not be disrupted.
3. If the port is **free**, proceed as normal.

For `--web-ui-only` mode, when the port is occupied:
- Print the same warning to stderr.
- Exit with code `1` (the user explicitly requested the dashboard; failure is fatal).

### 3.3 Thread-level guard

Wrap `run_server` body in a `try/except OSError` so that a race condition between check and
bind does not produce an unhandled exception in the daemon thread (which would be silently lost):
- Catch `OSError` in `run_server` and log to stderr instead of crashing.

---

## 4. Acceptance Criteria

- [ ] AC1: When the requested Web UI port is occupied, wrapper prints a clear warning to stderr and continues as MCP-only mode — no crash, no unhandled exception.
- [ ] AC2: MCP stdio protocol output (stdout) remains valid JSON-RPC only — no error text leaks to stdout.
- [ ] AC3: In `--web-ui-only` mode, occupied port causes exit code `1` with a clear stderr message.
- [ ] AC4: If the port is free, behavior is unchanged from pre-fix.
- [ ] AC5: Unit tests cover: (a) occupied port in bridge+webui mode, (b) occupied port in webui-only mode, (c) free port normal path.
- [ ] AC6: No regression in existing `test_main_webui.py` or `test_main.py` tests.

---

## 5. Dependencies

- `src/mcpbridge_wrapper/webui/server.py` — add `is_port_available`
- `src/mcpbridge_wrapper/__main__.py` — add collision guard around Web UI startup

---

## 6. Out of Scope

- PID file / single-instance lock (may be a follow-up)
- Auto-incrementing port fallback (YAGNI)
- Killing stale processes automatically (dangerous, out of scope)
