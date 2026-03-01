# P2-T3: Fix double-spawn race condition when MCP client toggles rapidly

**Task ID:** P2-T3
**Status:** In Progress
**Priority:** P1
**Branch:** feature/P2-T3-spawn-lock
**Date:** 2026-03-01
**Depends on:** P2-T2 ✅

## Problem

When an MCP client (e.g. Zed) toggles the connection off/on rapidly, two proxy processes can start simultaneously. Both enter `_spawn_broker_if_needed`, find no broker running, and each spawns a daemon subprocess. Two competing daemons race to bind the Unix socket:
- One wins and becomes the real broker.
- The other crashes (EADDRINUSE or similar).
- The proxy whose daemon lost gets no broker and shows 0 tools.

The root cause is a TOCTOU (time-of-check-time-of-use) race between the liveness check and the `Popen` call.

## Solution

Add a filesystem-level exclusive lock around the spawn decision in `_spawn_broker_if_needed` using `fcntl.flock`:

1. Open (or create) a lock file at `pid_file.with_suffix(".lock")` — e.g. `~/.mcpbridge_wrapper/broker.lock`.
2. Acquire `LOCK_EX` via `run_in_executor` (avoids blocking the event loop).
3. Under the lock, re-check liveness (PID file + socket connect) — the double-check pattern.
4. If broker is now alive → release lock and return (connect path handles the rest).
5. If still absent → spawn daemon, poll for socket appearance with lock held.
6. Lock is released when the `with open(...)` block exits (including on crash — OS releases `flock` on fd close).

### Why `flock` on a separate lock file?

- `flock` requires an open fd; using a dedicated `.lock` file avoids interfering with the PID file's content.
- `flock(LOCK_EX)` is automatically released when the process dies → no stale-lock cleanup needed.
- The lock is held only during spawn + socket-poll window (bounded by `connect_timeout`, default 10s).

## Deliverables

### `src/mcpbridge_wrapper/broker/proxy.py`
- Add `import fcntl` at module level.
- Refactor `_spawn_broker_if_needed` to:
  - Derive `lock_file = pid_file.with_suffix(".lock")`.
  - Ensure parent directory exists with `mkdir(parents=True, exist_ok=True)`.
  - Use `with open(lock_file, "w") as lock_fd:` + `await loop.run_in_executor(None, fcntl.flock, lock_fd.fileno(), fcntl.LOCK_EX)`.
  - Move all liveness checks and spawn logic inside the `with` block.

### `tests/unit/test_broker_proxy.py`
- Add `TestBrokerProxySpawnLock` class with:
  - `test_spawn_lock_file_created_next_to_pid_file` — lock file at expected path.
  - `test_spawn_acquires_exclusive_lock` — `fcntl.flock` called with `LOCK_EX`.
  - `test_second_proxy_skips_spawn_after_first_succeeds` — sequential simulation: second call finds socket alive under lock, skips `Popen`.

## Acceptance Criteria

- [ ] Rapid double-toggle produces exactly one broker daemon (second proxy detects liveness under lock and skips spawn)
- [ ] Lock is released on proxy exit (including crash) — guaranteed by `flock` kernel semantics
- [ ] All existing broker proxy tests pass
- [ ] New lock tests pass

## Implementation Notes

- `fcntl` is Unix/macOS only — acceptable since this project targets macOS exclusively.
- `run_in_executor(None, ...)` uses the default `ThreadPoolExecutor`; the blocking `flock` call does not block the asyncio event loop.
- The lock file path (`broker.lock`) is derived from `pid_file` path: `pid_file.with_suffix(".lock")`.
- No changes needed to `BrokerConfig`, `__main__.py`, or README — purely internal to `proxy.py`.
