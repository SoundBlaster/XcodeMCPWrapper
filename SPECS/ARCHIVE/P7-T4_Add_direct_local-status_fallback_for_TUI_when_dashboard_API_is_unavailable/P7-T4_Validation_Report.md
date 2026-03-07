# P7-T4 Validation Report — Add direct local-status fallback for TUI when dashboard API is unavailable

**Date:** 2026-03-07
**Branch:** `codex/p7-t4-local-status-fallback`
**Verdict:** PASS

---

## Summary of Changes

### `src/mcpbridge_wrapper/tui.py`

- Added `_build_local_fallback_broker()` helper: constructs a bounded local-only broker view from
  PID/socket/version files when the dashboard API is unavailable. Distinguishes between:
  - `running (local fallback)` — PID alive and visible to the process table
  - `stale local state` — PID or version files exist but the process is not running
  - `None` — no local state at all
- Updated `BrokerTUIClient.fetch_snapshot()` to call `_build_local_fallback_broker()` before
  probing the dashboard. When `probe_backend()` raises, the snapshot is built from local state
  with `runtime_source` set to `"local-fallback"` (broker data available) or
  `"dashboard-unavailable"` (no local broker data).
- Added `_read_local_pid()` and `_read_local_version()` helpers for PID liveness check and
  version file reading.
- Updated `BrokerTUISnapshot` with new fields: `local_pid`, `local_daemon_running`,
  `local_socket_present`, `local_daemon_version`, `local_pid_file`, `local_socket_path`,
  `local_version_file`, `runtime_source`, `error_message`, `status_message`.
- Updated `render_screen()` to:
  - Always show a "Local Broker Files" section with PID/socket/version from local state.
  - Label runtime source as `"local broker files only"`, `"no reachable dashboard data"`, or
    `"live dashboard API"`.
  - Show banner messages when in local fallback mode indicating dashboard unavailability and
    that live control is not available.
- Updated `BrokerTUI._run_loop()` to emit a clear message when 's' is pressed in local-fallback
  mode instead of silently doing nothing.

### `tests/unit/test_tui.py`

Added targeted tests for all new fallback paths:

- `test_fetch_snapshot_builds_local_fallback_when_broker_is_running` — running PID → `local-fallback`
- `test_fetch_snapshot_builds_stale_local_fallback_when_files_remain` — stale files → `local-fallback`
- `test_fetch_snapshot_surfaces_runtime_errors` — no local state → `dashboard-unavailable`
- `test_render_screen_shows_local_fallback_source_and_control_state` — screen labels
- `test_run_loop_does_not_call_stop_without_live_control` — 's' key in fallback mode

---

## Targeted Tests

```
tests/unit/test_tui.py::TestBrokerTUIClient::test_fetch_snapshot_builds_local_fallback_when_broker_is_running PASSED
tests/unit/test_tui.py::TestBrokerTUIClient::test_fetch_snapshot_builds_stale_local_fallback_when_files_remain PASSED
tests/unit/test_tui.py::TestBrokerTUIClient::test_fetch_snapshot_surfaces_runtime_errors PASSED
tests/unit/test_tui.py::TestRenderScreen::test_render_screen_shows_local_fallback_source_and_control_state PASSED
tests/unit/test_tui.py::TestBrokerTUI::test_run_loop_does_not_call_stop_without_live_control PASSED
```

All 38 TUI tests pass.

---

## Full Quality Gate Results

### `pytest` — all tests
```
898 passed, 5 skipped, 2 warnings in 8.10s
```

### `ruff check src/`
```
All checks passed!
```

### `mypy src/`
```
Success: no issues found in 20 source files
```

### `pytest --cov` — coverage
```
TOTAL: 91.75% (threshold: 90%) — PASS
tui.py: 96.1%
```

---

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| TUI useful when dashboard API unavailable | PASS — local fallback snapshot shown |
| Screen distinguishes live dashboard from local fallback | PASS — `Runtime Source` label + banners |
| Users can infer broker state from TUI alone | PASS — state field shows `running (local fallback)` or `stale local state` |
| Stop control clearly unavailable in fallback mode | PASS — key 's' shows informational message |
| All tests pass | PASS — 898/898 |
| Ruff clean | PASS |
| Mypy clean | PASS |
| Coverage ≥ 90% | PASS — 91.75% |
