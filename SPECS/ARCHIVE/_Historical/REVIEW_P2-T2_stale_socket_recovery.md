## REVIEW REPORT — P2-T2 Stale Socket Recovery

**Scope:** origin/main..HEAD
**Files:** 4 (proxy.py, daemon.py, test_broker_proxy.py, test_broker_daemon.py)
**Date:** 2026-03-01

---

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] Blocking socket connect inside async context**

In `proxy.py` → `_spawn_broker_if_needed`, the liveness check uses `socket.socket(AF_UNIX, ...)` with `s.settimeout(1.0)` — a synchronous blocking call inside an `async def` function. If the daemon is hung (not refusing but also not accepting), the event loop is blocked for up to 1 second.

In practice, Unix domain socket connects on the local machine are instantaneous; the timeout protects against edge cases. For broker mode, the 1-second block is acceptable given that:
- `_spawn_broker_if_needed` is called once per proxy session start
- The hang scenario (listening socket not accepting) is extremely rare with broker

**Fix (optional, lower priority):** Could be converted to an async probe via `asyncio.open_unix_connection` with `asyncio.wait_for`. Defer unless profiling shows impact.

---

**[Nit] atexit handler not deregistered after clean stop**

In `daemon.py`, `atexit.register(self._cleanup_files)` is called on successful start. After `stop()` completes and removes files, the atexit handler remains registered. On interpreter exit after a clean shutdown, `_cleanup_files` runs again on already-absent files.

This is safe because `_cleanup_files` uses `unlink(missing_ok=True)`. However, repeated registration across multiple `start()`/`stop()` cycles (not currently possible due to PID file locking, but possible in tests) would accumulate atexit registrations.

**Fix (optional):** Use `atexit.unregister(self._cleanup_files)` in `stop()`. Low priority — current behavior is safe.

---

### Architectural Notes

- The catch-all `except OSError` in `_spawn_broker_if_needed` handles `ConnectionRefusedError`, `FileNotFoundError` (TOCTOU: socket disappears between `exists()` and `connect()`), and `OSError: [Errno 38] Socket operation on non-socket` (connecting to a regular file). This is the correct breadth of coverage.
- The atexit approach complements the existing SIGTERM/SIGINT handlers in `run_forever()`. The combination means clean files are guaranteed on: normal exit, `sys.exit()`, SIGTERM, SIGINT. Only SIGKILL (non-interceptable) leaves stale files — which the new proxy liveness check now handles automatically.
- The existing `test_spawn_noop_when_socket_exists` test was correctly updated to mock `socket.connect()` success rather than relying on a plain `touch()`'d file (which would have produced an `OSError` with the new code).

---

### Tests

- 4 new tests added (3 for stale socket proxy scenarios, 1 for atexit daemon registration).
- 1 existing test updated to reflect new liveness-check semantics.
- All 719 tests pass; coverage 91.78% (≥ 90%).
- **Gap (Low priority):** No explicit test for TOCTOU race (socket file disappears between `exists()` and `connect()`). Covered implicitly by `except OSError` but not explicitly tested.

---

### Next Steps

- **P2-T3** (P1, now unblocked by P2-T2 ✅): Fix double-spawn race condition with `fcntl.flock` spawn lock
- **Optional** (Nit): Add `atexit.unregister` in `daemon.stop()` if test-cycle isolation becomes an issue
- **Optional** (Low): Convert blocking socket probe to async `open_unix_connection` + `wait_for`
