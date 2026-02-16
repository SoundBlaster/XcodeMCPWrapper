# P13-T2: Implement Persistent Broker Daemon with Single Upstream Xcode Bridge

**Phase:** 13 — Persistent Broker & Shared Xcode Session
**Priority:** P0
**Status:** In Progress
**Branch:** feature/P13-T2-broker-daemon
**Created:** 2026-02-16

---

## 1. Objective

Replace the `BrokerDaemon` stub in `src/mcpbridge_wrapper/broker/daemon.py` with
a fully working implementation that:

1. Launches one `xcrun mcpbridge` subprocess and keeps it alive.
2. Prevents duplicate instances via PID-file locking.
3. Handles upstream crashes with exponential-backoff reconnection.
4. Provides graceful shutdown (drain in-flight requests, clean socket/PID files).

---

## 2. Deliverables

| Artifact | Description |
|----------|-------------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Full `BrokerDaemon` implementation |
| `tests/unit/test_broker_daemon.py` | Unit tests for all acceptance criteria |
| `SPECS/INPROGRESS/P13-T2_Validation_Report.md` | Validation report |

---

## 3. Implementation Plan

### 3.1 `BrokerDaemon.start()`

```
1. Ensure data dir exists (mkdir -p ~/.mcpbridge_wrapper/)
2. Stale-lock check:
   a. If PID file exists:
      - Read PID.
      - kill -0 <pid> → if alive: raise RuntimeError("already running")
      - If dead: remove stale PID + socket files
3. Create/bind Unix socket (mode 0600)
4. Write PID file (own PID)
5. Launch upstream: asyncio.create_subprocess_exec(*config.upstream_cmd,
       stdin=PIPE, stdout=PIPE, stderr=sys.stderr)
6. Transition state: INIT → READY
7. Start background tasks:
   - _read_upstream_loop()  — reads JSON-RPC lines from upstream stdout
```

### 3.2 `BrokerDaemon.stop()`

```
1. Transition state → STOPPING
2. Cancel pending requests with JSON-RPC error -32000 (shutdown)
3. Wait up to config.graceful_shutdown_timeout for in-flight tasks
4. Close upstream stdin (send EOF), wait for process to exit
5. Remove socket file and PID file
6. Transition state → STOPPED
```

### 3.3 `BrokerDaemon.run_forever()`

```
1. Call start()
2. Register SIGTERM / SIGINT handlers → call stop()
3. await until state == STOPPED
```

### 3.4 `_read_upstream_loop()`

```
Loop:
  line = await upstream.stdout.readline()
  if EOF:
    if state == STOPPING: break
    → trigger reconnect
  else:
    → parse JSON, route response (P13-T3 will handle routing; daemon just reads)
```

### 3.5 Reconnection

```
attempt = 0
while state == RECONNECTING:
  delay = min(2 ** attempt, config.reconnect_backoff_cap)
  await asyncio.sleep(delay)
  try:
    launch new upstream
    state = READY
    break
  except OSError:
    attempt += 1
```

### 3.6 Status / Health

Add `status()` method that returns a dict:
```python
{"state": daemon.state.value, "pid": os.getpid(), "upstream_pid": upstream.pid}
```

---

## 4. Acceptance Criteria

- [ ] Starting broker twice does not spawn duplicate upstream bridge instances
- [ ] Broker survives client disconnects without restarting upstream bridge
  _(validated by tests that mock client disconnects and confirm upstream still running)_
- [ ] Graceful shutdown terminates upstream process and cleans lock/socket files
- [ ] Crash recovery path is covered by tests (upstream EOF triggers RECONNECTING → READY)

---

## 5. Quality Gates

- `pytest tests/unit/test_broker_daemon.py -v` — all pass
- `pytest --cov` — coverage ≥ 90 %
- `ruff check src/` — no errors
- `mypy src/` — no errors (if configured)

---

## 6. Dependencies

| Dependency | Status |
|------------|--------|
| P13-T1: Architecture design + stubs | ✅ Complete |
| `bridge.py`: Subprocess creation patterns | ✅ Available |
