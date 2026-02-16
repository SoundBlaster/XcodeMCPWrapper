## REVIEW REPORT — P13-T2 Broker Daemon Implementation

**Scope:** origin/main..HEAD (feature/P13-T2-broker-daemon)
**Files:** 4 changed (daemon.py, test_broker_daemon.py, test_broker_stubs.py, Workplan/archive docs)
**Date:** 2026-02-17

---

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

**Overall:** The implementation is correct and well-tested. Three low/nit-level observations noted below; none are blockers.

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `_read_upstream_loop` reassigns `line` variable to itself (unused mutation)**

In `daemon.py` lines ~260-262:
```python
line = raw.decode() if isinstance(raw, bytes) else raw
line = line.rstrip("\n")
```
The `line` variable is logged and JSON-parsed but never forwarded (routing is deferred to P13-T3). This is intentional per the PRD scope, but the decode+strip logic runs on every message even though the result is only used for debug logging and JSON validation. No bug; purely a performance nit.

**Fix suggestion (deferred):** When P13-T3 adds routing, fold the decode/strip into the routing path. No immediate action needed.

---

**[Low] `run_forever()` busy-polls with `asyncio.sleep(0.1)`**

```python
while self._state not in (BrokerState.STOPPED, BrokerState.STOPPING):
    await asyncio.sleep(0.1)
```
A 100ms polling interval introduces up to 100ms of stop-signal latency. For a long-lived daemon this is fine (<<1s), but an `asyncio.Event` would be more idiomatic.

**Fix suggestion (deferred to follow-up):** Replace polling loop with `await self._stop_event.wait()` after registering SIGTERM.

---

**[Nit] `# type: ignore[type-arg]` on `asyncio.Task`**

```python
self._read_task: asyncio.Task | None = None  # type: ignore[type-arg]
```
This suppresses a mypy error for the unparameterised `asyncio.Task`. Since mypy is not configured as a hard gate yet, this is acceptable. Can be resolved with `asyncio.Task[None]` when mypy is enforced.

---

### Architectural Notes

- **P13-T3 integration point is clean.** The `_read_upstream_loop` currently only logs and discards JSON lines; the routing hook is clearly marked with a comment. No refactoring of the loop signature is needed when P13-T3 adds a `_route_response()` call.
- **`_stop_event` is created in `__init__`**, not in `start()`. This means calling `start()` a second time (after a `stop()`) without recreating the daemon will find `_stop_event` already set and the loop will exit immediately. The current design assumes single-use daemon instances, which is consistent with the PID-file model.  Documented for P13-T3 awareness.
- **PID file is written before the upstream subprocess is launched.** A crash between `pid_file.write_text()` and `_launch_upstream()` leaves a live PID file pointing to the current process but with no upstream. Subsequent `start()` calls on a new daemon instance would see the live PID and refuse to start even though there is no active broker. This is an acceptable edge case for v1; a more robust approach (write PID after successful upstream launch) is deferred.

---

### Tests

- 26 new tests in `test_broker_daemon.py` covering all acceptance criteria.
- 3 tests removed from `test_broker_stubs.py` (`NotImplementedError` assertions that are no longer valid post-P13-T2 implementation).
- Broker module coverage: **93.2%** (≥90% required ✅).
- Uncovered lines: mostly signal-handler closure paths and edge branches in reconnect logic that require OS-level signal injection; acceptable for unit test scope.

---

### Next Steps

1. **P13-T3** (P0) — Implement `UnixSocketServer` with client connection accept loop and JSON-RPC multiplexing. Will integrate with `_read_upstream_loop` via a `_route_response()` hook.
2. **FU-P13-T2-1 (optional)** — Replace `run_forever()` polling loop with `asyncio.Event`-based wait to eliminate 100ms stop latency.
3. **FU-P13-T2-2 (optional)** — Move `pid_file.write_text()` to after successful upstream launch to close the write-before-launch edge case.
