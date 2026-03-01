# P2-T1: Replace --broker-spawn/--broker-connect with single --broker flag

**Task ID:** P2-T1
**Status:** In Progress
**Priority:** P1
**Branch:** feature/P2-T1-broker-flag
**Date:** 2026-03-01

## Problem

Users currently must choose between two broker flags with overlapping and confusing semantics:
- `--broker-spawn` — auto-start daemon if absent, then connect
- `--broker-connect` — require daemon already running, connect only

This distinction is invisible to most users who simply want "broker mode". It forces them to know internal daemon lifecycle details before they can configure their MCP client.

## Solution

Add a single `--broker` flag that auto-detects the right action:
- If a live broker is already running → connect to it
- If no broker is running → spawn one, then connect

This is exactly the behavior `--broker-spawn` already implements via `BrokerProxy._spawn_broker_if_needed`. So `--broker` is a user-facing alias for `--broker-spawn`.

Keep `--broker-spawn` and `--broker-connect` working unchanged for backwards compatibility.

## Deliverables

1. **`src/mcpbridge_wrapper/__main__.py`**
   - `_parse_broker_args`: recognise `--broker` as equivalent to `--broker-spawn`
   - `main()`: no logic change needed (same code path as `--broker-spawn`)

2. **`README.md`**
   - Replace all `--broker-spawn` in MCP settings examples with `--broker`
   - Keep mention of `--broker-connect` in the reference section as a legacy alias

3. **`tests/unit/test_main.py`**
   - Add tests for `--broker` in `_parse_broker_args`
   - Add test for `main()` with `--broker` constructing `BrokerProxy(auto_spawn=True)`

## Acceptance Criteria

- [ ] `--broker` flag auto-connects when daemon is alive, spawns when absent (via existing proxy logic)
- [ ] `--broker-spawn` and `--broker-connect` still work unchanged
- [ ] All MCP settings examples in README use `--broker`
- [ ] All existing tests pass
- [ ] New tests for `--broker` flag pass

## Implementation Notes

- No logic change to `BrokerProxy` — `auto_spawn=True` already handles the detect-then-spawn behaviour introduced in P2-T2.
- `_parse_broker_args` returns `(broker_daemon, broker_connect, broker_spawn, remaining)`. Adding `--broker` means: set `broker_spawn = True` and `broker_connect = True`, identical to `--broker-spawn`.
- README lines to update: lines 61, 78, 273, 289, 386, 391, 433, 438 (approximate, verify exact grep output).

## Dependencies

- P2-T2 (stale socket recovery) ✅ — ensures `--broker`/`auto_spawn=True` reliably recovers from stale sockets.
