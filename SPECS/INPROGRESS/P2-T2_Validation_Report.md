# P2-T2 Validation Report

**Task:** Self-healing stale socket and PID file recovery
**Date:** 2026-03-01
**Branch:** feature/P2-T2-stale-socket-recovery
**Verdict:** PASS

---

## Quality Gate Results

| Gate | Result | Details |
|------|--------|---------|
| `ruff check src/` | ✅ PASS | All checks passed |
| `pytest` | ✅ PASS | 719 passed, 5 skipped |
| `pytest --cov` | ✅ PASS | 91.78% coverage (≥ 90% required) |
| `mypy src/` | N/A | Not configured |

---

## Changes Made

### `src/mcpbridge_wrapper/broker/proxy.py`

- Added `import socket` at module level (replaces inline import-inside-function approach)
- Replaced plain `socket_path.exists()` guard in `_spawn_broker_if_needed` with a connect-based liveness check:
  - If socket file exists and `connect()` succeeds → broker is alive, skip spawn
  - If socket file exists and `connect()` raises `OSError` (covers `ConnectionRefusedError`, `OSError: socket operation on non-socket`, timeouts) → treat as stale, remove both socket and PID files, fall through to spawn

### `src/mcpbridge_wrapper/broker/daemon.py`

- Added `import atexit` at module level
- Registered `self._cleanup_files` with `atexit` in `start()` after the transport is successfully started, ensuring socket/PID files are removed even on abnormal interpreter exits (unhandled exceptions, `sys.exit()`). SIGKILL cannot be intercepted and is not covered.

---

## Tests Added / Updated

### `tests/unit/test_broker_proxy.py`

- **Updated** `TestBrokerProxyAutoSpawn::test_spawn_noop_when_socket_exists` — now mocks `socket.socket.connect()` to succeed (simulating a live broker) instead of relying on the old existence-only check.

- **Added** `TestBrokerProxyStaleSocket` class with 3 tests:
  - `test_stale_socket_triggers_spawn` — socket file exists, `connect()` raises `ConnectionRefusedError` → `Popen` is called
  - `test_stale_socket_removes_files` — socket and PID files are removed before spawn attempt
  - `test_live_socket_skips_spawn` — socket file exists, `connect()` succeeds → `Popen` NOT called

### `tests/unit/test_broker_daemon.py`

- **Added** `TestBrokerDaemonAtExit` class with 1 test:
  - `test_atexit_registered_after_start` — verifies `atexit.register` is called with `_cleanup_files` during `start()`

---

## Acceptance Criteria Status

- [x] After broker crash, next `--broker-spawn` session auto-recovers without manual file removal
- [x] Liveness check uses `connect()` not `exists()`
- [x] Daemon registers `atexit` cleanup on `start()`
- [x] All existing broker tests pass (719 passed, 5 skipped)
- [x] New tests cover the stale-socket scenario and atexit registration
- [x] `ruff check src/` passes
- [x] Coverage ≥ 90%
