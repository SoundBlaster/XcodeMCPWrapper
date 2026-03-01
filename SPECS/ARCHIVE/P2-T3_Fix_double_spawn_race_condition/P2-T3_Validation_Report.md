# P2-T3 Validation Report

**Task:** Fix double-spawn race condition when MCP client toggles rapidly
**Date:** 2026-03-01
**Verdict:** PASS

## Acceptance Criteria

- [x] Rapid double-toggle produces exactly one broker daemon — second proxy re-checks liveness under lock and skips Popen (verified by `test_second_proxy_skips_spawn_after_first_succeeds`)
- [x] Lock is released on proxy exit including crash — guaranteed by `flock` kernel semantics + `with open(...)` context manager (verified by `test_lock_released_on_timeout`)
- [x] All existing broker proxy tests pass (26/26 in `test_broker_proxy.py`)
- [x] New lock tests pass (4 new tests in `TestBrokerProxySpawnLock`)

## Changes Made

### `src/mcpbridge_wrapper/broker/proxy.py`
- Added `import fcntl` at module level.
- `_spawn_broker_if_needed`: wrapped entire body in `with open(lock_file, "w") as lock_fd:` + `await loop.run_in_executor(None, fcntl.flock, lock_fd.fileno(), fcntl.LOCK_EX)`.
- Lock file path: `pid_file.with_suffix(".lock")` — e.g. `~/.mcpbridge_wrapper/broker.lock`.
- Added `lock_file.parent.mkdir(parents=True, exist_ok=True)` for first-run safety.
- Updated docstring to explain the lock semantics.

### `tests/unit/test_broker_proxy.py`
- Added `TestBrokerProxySpawnLock` class with 4 tests:
  - `test_spawn_lock_file_created_next_to_pid_file`
  - `test_spawn_acquires_exclusive_lock`
  - `test_second_proxy_skips_spawn_after_first_succeeds`
  - `test_lock_released_on_timeout`

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/unit/` | 682 passed, 2 warnings |
| `ruff check src/` | All checks passed |
| `pytest --cov` | 91.43% (≥ 90% required) |
