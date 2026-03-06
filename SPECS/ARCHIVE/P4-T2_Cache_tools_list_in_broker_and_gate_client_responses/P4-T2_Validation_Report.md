# P4-T2 Validation Report

**Task:** P4-T2 — Cache tools/list in broker and gate client responses on upstream readiness
**Date:** 2026-03-06
**Verdict:** PASS

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest` (782 passed, 5 skipped) | ✅ PASS |
| Coverage ≥ 90% | ✅ PASS (91.0%) |
| `ruff check src/` | ✅ PASS |
| `mypy src/` | ✅ PASS |

## Acceptance Criteria

- [x] Broker sends `initialize` probe (id=0) to upstream immediately after `_launch_upstream()`
- [x] `_upstream_initialized` event is set only after the probe response is received
- [x] `_upstream_initialized` is cleared at the start of each reconnect attempt
- [x] Client `tools/list` request is served from `_tools_list_cache` if cache is populated
- [x] `_tools_list_cache` is cleared on upstream EOF/reconnect and refreshed after re-init
- [x] Client requests with `is_notification=False` are gated on `_upstream_initialized` with TTL
- [x] TTL expiry returns JSON-RPC error -32001 to the client (not an empty response)
- [x] All existing quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, coverage ≥ 90%

## Changes Delivered

### `src/mcpbridge_wrapper/broker/daemon.py`
- Added `_BROKER_INIT_ID = 0` and `_BROKER_TOOLS_ID = -1` module-level constants
- Added `_upstream_initialized: asyncio.Event` and `_tools_list_cache: str | None` to `__init__`
- Added `upstream_initialized` property
- Added `_send_broker_probes()` coroutine (sends initialize probe with id=0)
- Modified `start()` to call `_send_broker_probes()` after `_launch_upstream()`
- Modified `_read_upstream_loop()` to intercept id=0 (sets event, sends tools probe) and id=-1 (caches result)
- Modified `_reconnect()` to clear event and cache, re-send probes after reconnect

### `src/mcpbridge_wrapper/broker/transport.py`
- Replaced RECONNECTING polling loop with `asyncio.wait_for` gate on `upstream_initialized.wait()`
- Added `tools/list` cache hit path (serves from cache, skips upstream forwarding)
- TTL expiry returns `-32001 "Broker upstream not ready — request TTL exceeded"`

### `tests/unit/test_broker_daemon.py`
- Added `TestBrokerReadinessGate` class (5 new tests):
  - `test_upstream_initialized_event_set_on_init_probe_response`
  - `test_tools_list_probe_sent_after_init_probe_acked`
  - `test_tools_list_cache_populated_on_probe_response`
  - `test_upstream_initialized_cleared_on_reconnect`
  - `test_send_broker_probes_noop_when_no_upstream`

### `tests/unit/test_broker_transport.py`
- Updated `_make_daemon_mock` to set pre-set `upstream_initialized` event and `_tools_list_cache = None`
- Rewrote `TestQueueTTL` class (2 tests: TTL timeout, gate success)
- Updated `test_reconnecting_then_unavailable_returns_32001` to use new gate design
- Added `TestToolsListCache` class (3 new tests): cache hit (int ID), cache hit (string ID), cache miss
