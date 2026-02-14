# BUG-T6 Validation Report

**Task:** BUG-T6 — Web UI port collisions (`--web-ui-port`) create unstable multi-process behavior
**Date:** 2026-02-14
**Verdict:** ✅ PASS

---

## Quality Gates

| Gate | Command | Result |
|------|---------|--------|
| Unit tests | `pytest tests/unit/` | ✅ 323 passed, 0 failed |
| Linting | `ruff check src/` | ✅ All checks passed |
| Type checking | `mypy src/` | ✅ Success: no issues found in 12 source files |

---

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| AC1 | When port occupied, wrapper prints warning and continues as MCP-only — no crash | ✅ | `test_occupied_port_in_bridge_mode_skips_webui` passes; `run_server` OSError caught |
| AC2 | MCP stdout remains valid JSON-RPC only | ✅ | Warning printed to `sys.stderr`; stdout unaffected |
| AC3 | `--web-ui-only` mode with occupied port exits with code 1 + clear message | ✅ | `test_occupied_port_in_webui_only_mode_exits_with_error` passes |
| AC4 | Free port: behavior unchanged from pre-fix | ✅ | `test_free_port_starts_webui_normally` passes; all 36 pre-existing tests pass |
| AC5 | Tests cover (a) occupied/bridge, (b) occupied/webui-only, (c) free port, (d) `is_port_available` unit tests | ✅ | 5 new tests in `TestPortCollisionHandling` |
| AC6 | No regressions in existing test suite | ✅ | 323/323 pass |

---

## Changes

### `src/mcpbridge_wrapper/webui/server.py`
- Added `import socket` and `import sys`
- Added `is_port_available(host, port) -> bool` — attempts `socket.bind()` and returns `False` on `OSError`
- Wrapped `uvicorn.run(...)` in `try/except OSError` to catch race-condition bind failures in the daemon thread

### `src/mcpbridge_wrapper/__main__.py`
- Imports `is_port_available` from `webui.server`
- Before `--web-ui-only` server start: check port; if occupied, print error and `return 1`
- Before `run_server_in_thread`: check port; if occupied, print warning and skip Web UI; MCP bridge starts normally

### `tests/unit/test_main_webui.py`
- Added `patch("mcpbridge_wrapper.webui.server.is_port_available", return_value=True)` to 4 existing tests that previously relied on real port availability
- Added `class TestPortCollisionHandling` with 5 new tests
