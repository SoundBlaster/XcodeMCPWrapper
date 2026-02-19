# PRD: FU-P13-T13 — Make broker startup transactional when transport bind/start fails

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Dependencies:** P13-T2 (✅), P13-T3 (✅)

---

## 1. Objective

Make `BrokerDaemon.start()` fully transactional: if any step after the upstream
subprocess is launched fails (transport bind error, PID file write error, etc.),
perform a complete rollback — terminate the upstream, cancel the read task,
remove PID/socket files — so the broker always ends up in a clean STOPPED state
with no orphaned processes or stale files.

---

## 2. Background & Current State

### 2.1 What exists

```python
async def start(self) -> None:
    self._check_and_clear_stale_lock()
    await self._launch_upstream()           # A: upstream subprocess running
    self._config.pid_file.write_text(...)   # B: PID file written
    self._state = BrokerState.READY         # C: state changed too early
    self._read_task = asyncio.ensure_future(...)  # D: read loop started
    if self._transport is not None:
        await self._transport.start()       # E: can raise OSError — no rollback!
```

If step **E** raises (e.g., `[Errno 98] Address already in use`):
- The upstream subprocess is **running** but unmanaged.
- The PID file **exists**.
- The read task is **running**.
- The broker state is `READY` (incorrect).

Result: zombie upstream process, stale PID file, no way to connect clients.

### 2.2 Target state

All failures after step **A** trigger `_rollback_startup()`:
- Cancel and await the read task (if started).
- Terminate and await the upstream subprocess.
- Remove PID and socket files.
- Set state to `STOPPED`.
- Re-raise the original exception so the caller knows startup failed.

---

## 3. Acceptance Criteria

- [ ] If `transport.start()` raises, upstream subprocess is terminated and fully waited.
- [ ] If `transport.start()` raises, PID and socket files are removed.
- [ ] Broker state is `STOPPED` after any rollback.
- [ ] The original exception from `transport.start()` propagates out of `BrokerDaemon.start()`.
- [ ] If `pid_file.write_text()` raises, upstream is also rolled back.
- [ ] Unit tests cover all rollback scenarios.
- [ ] Quality gates: `pytest`, `ruff check src/`, `mypy src/` all pass.

---

## 4. Implementation Plan

### Phase A — Tests first (TDD)

**File:** `tests/unit/test_broker_daemon.py`

New test class `TestStartupRollback`:

1. `test_transport_start_failure_terminates_upstream`
   — Mock `transport.start()` to raise `OSError("addr in use")`.
   — Assert `upstream.terminate()` called, `upstream.wait()` awaited.

2. `test_transport_start_failure_removes_pid_file`
   — Same mock. Assert PID file does not exist after `start()` raises.

3. `test_transport_start_failure_removes_socket_file`
   — Same mock. Assert socket file does not exist after `start()` raises.

4. `test_transport_start_failure_state_is_stopped`
   — Same mock. Assert `daemon.state == BrokerState.STOPPED`.

5. `test_transport_start_failure_reraises_exception`
   — Same mock. Assert `start()` raises the original `OSError`.

6. `test_pid_write_failure_terminates_upstream`
   — Mock `pid_file.write_text` to raise `OSError`.
   — Assert upstream is terminated and state is STOPPED.

### Phase B — Implementation

**File:** `src/mcpbridge_wrapper/broker/daemon.py`

#### B-1. Restructure `start()` with try/except rollback

```python
async def start(self) -> None:
    self._config.socket_path.parent.mkdir(parents=True, exist_ok=True)
    self._check_and_clear_stale_lock()
    await self._launch_upstream()

    try:
        self._config.pid_file.write_text(str(os.getpid()))
        logger.debug("PID file written: %s", self._config.pid_file)

        self._stop_event.clear()
        self._stopped_event.clear()
        self._read_task = asyncio.ensure_future(self._read_upstream_loop())

        if self._transport is not None:
            await self._transport.start()

    except Exception:
        await self._rollback_startup()
        raise

    self._state = BrokerState.READY
    logger.info(
        "Broker READY (upstream PID %s)",
        self._upstream.pid if self._upstream else "?",
    )
```

Key change: `self._state = BrokerState.READY` is now **after** the transport
starts (and only reached if no exception is raised).

#### B-2. Add `_rollback_startup()` private method

```python
async def _rollback_startup(self) -> None:
    """Roll back a failed startup: cancel read task, kill upstream, clean files."""
    logger.warning("Rolling back failed broker startup.")

    # Cancel read task
    if self._read_task is not None and not self._read_task.done():
        self._read_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await self._read_task
        self._read_task = None

    # Terminate upstream
    if self._upstream is not None and self._upstream.returncode is None:
        with contextlib.suppress(Exception):
            self._upstream.terminate()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(
                self._upstream.wait(),
                timeout=self._config.graceful_shutdown_timeout,
            )
        if self._upstream.returncode is None:
            with contextlib.suppress(Exception):
                self._upstream.kill()
            with contextlib.suppress(Exception):
                await self._upstream.wait()
    self._upstream = None

    # Clean up files
    self._cleanup_files()
    self._state = BrokerState.STOPPED
```

### Phase C — Troubleshooting documentation

**File:** `docs/troubleshooting.md`

Add a note under broker mode:

> **Broker fails to start with "Address already in use"**: A previous broker
> instance may have left a stale socket file. Since v0.3.x, a failed startup
> performs automatic cleanup. If the error persists, check for a running broker
> with `cat ~/.mcpbridge_wrapper/broker.pid` and stop it first.

---

## 5. Files Changed

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Restructure `start()` with rollback try/except; add `_rollback_startup()` |
| `tests/unit/test_broker_daemon.py` | New `TestStartupRollback` class (6 tests) |
| `docs/troubleshooting.md` | Add broker startup failure troubleshooting note |

---

## 6. Notes

- `_state` must only be set to `READY` after ALL startup steps succeed.
- `_rollback_startup()` must be idempotent: safe to call even if upstream was never launched.
- The `_rollback_startup()` timeout uses `config.graceful_shutdown_timeout` (same as `stop()`).
- Do not call `_cleanup_files()` in the `_rollback_startup()` if a socket file was never created (i.e., if transport never started). `_cleanup_files()` uses `missing_ok=True`, so this is safe regardless.
