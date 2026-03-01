# P2-T2: Self-healing stale socket and PID file recovery

**Status:** In Progress
**Priority:** P0
**Branch:** feature/P2-T2-stale-socket-recovery
**Created:** 2026-03-01

---

## Problem Statement

When the broker daemon crashes or is killed, it leaves `broker.sock` and `broker.pid` on disk. The proxy's `_spawn_broker_if_needed` checks `socket_path.exists()` and skips spawning if the socket file is present — even if no process is listening. This silently blocks all future broker mode sessions until the user manually deletes the files.

---

## Root Cause

In `proxy.py` → `_spawn_broker_if_needed`, line 131-133:

```python
# Check if socket already exists (race condition: broker started without PID file yet)
if socket_path.exists():
    logger.debug("Broker socket already present; skipping spawn.")
    return
```

Existence check (`Path.exists()`) does not verify whether anything is actually listening on the socket. A stale socket file left after a crash passes the existence check and prevents spawn.

---

## Solution

### 1. `proxy.py` — Liveness check in `_spawn_broker_if_needed`

Replace the plain existence check with a socket connect attempt:

```python
if socket_path.exists():
    import socket as _socket
    try:
        with _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(str(socket_path))
        # Connection succeeded → broker is alive
        logger.debug("Broker socket present and accepting connections; skipping spawn.")
        return
    except ConnectionRefusedError:
        # Stale socket — broker is not listening
        logger.warning(
            "Stale socket found (broker not accepting connections); removing stale files."
        )
        socket_path.unlink(missing_ok=True)
        pid_file.unlink(missing_ok=True)
        # Fall through to spawn
```

This ensures:
- If broker is alive (socket accepts connections): skip spawn (no change in behaviour)
- If broker is dead (socket refuses connections): remove stale files and proceed with spawn
- `FileNotFoundError` and other OS errors during connect are suppressed — treated as "not alive" (also falls through to spawn path)

### 2. `daemon.py` — `atexit` cleanup on daemon exit

The daemon already removes files via `_cleanup_files()` in `stop()`, and `stop()` is called by the SIGTERM/SIGINT handlers in `run_forever()`. However, if the Python interpreter exits abnormally (e.g., unhandled exception, explicit `sys.exit()`), cleanup may be skipped.

Add an `atexit` registration in `start()`:

```python
import atexit
atexit.register(self._cleanup_files)
```

This ensures `_cleanup_files()` runs even for abnormal exits (excluding SIGKILL, which cannot be intercepted).

---

## Files to Change

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Replace existence-only socket check with connect-based liveness check |
| `src/mcpbridge_wrapper/broker/daemon.py` | Register `atexit` cleanup in `start()` |

---

## Tests to Add

In `tests/unit/test_broker_proxy.py` — new class `TestBrokerProxyStaleSocket`:

1. **`test_stale_socket_triggers_spawn`** — socket file exists but connect raises `ConnectionRefusedError`; verify `Popen` is called and stale files are removed.
2. **`test_live_socket_skips_spawn`** — socket file exists and connect succeeds; verify `Popen` is NOT called.
3. **`test_stale_socket_with_stale_pid_file_triggers_spawn`** — both files exist, connect raises `ConnectionRefusedError`; verify both files are removed and spawn proceeds.

In `tests/unit/test_broker_daemon.py` — new class `TestBrokerDaemonAtExit`:

4. **`test_atexit_registered_after_start`** — after `daemon.start()`, `atexit` registry includes `_cleanup_files`.

---

## Acceptance Criteria

- [ ] After broker crash, next `--broker-spawn` session auto-recovers without manual file removal
- [ ] Liveness check uses `connect()` not `exists()`
- [ ] Daemon registers `atexit` cleanup on `start()`
- [ ] All existing broker tests pass
- [ ] New tests cover the stale-socket scenario and atexit registration
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes (if configured)
- [ ] Coverage ≥ 90%

---

## Dependencies

None — can be implemented independently.
