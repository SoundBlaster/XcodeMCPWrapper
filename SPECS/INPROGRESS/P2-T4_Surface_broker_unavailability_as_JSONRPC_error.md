# PRD: P2-T4 — Surface broker unavailability as JSON-RPC error instead of silent timeout

## Overview

When `BrokerProxy` cannot connect to the broker (timeout, spawn failure, daemon unavailable),
the client currently receives no response and eventually times out — showing "0 tools" or a
generic connection error with no actionable message. This task fixes the proxy to return a
well-formed JSON-RPC error response so MCP clients can surface a meaningful error.

## Problem Statement

`BrokerProxy.run()` calls `_spawn_broker_if_needed()` and then `_connect_with_timeout()`.
Both may raise `TimeoutError` or `OSError`. These exceptions currently propagate uncaught,
causing the proxy process to exit. The client's stdout pipe reaches EOF, but no JSON-RPC
response is ever written — the client hangs indefinitely or shows a confusing "0 tools" state.

## Proposed Solution

Wrap the connect phase in `run()` with a try/except. On any connection failure:

1. Log the error.
2. Write a JSON-RPC 2.0 error response to stdout (before exiting).
3. Return cleanly (no re-raise).

### Error response format

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32001,
    "message": "Broker unavailable: <reason>"
  }
}
```

`id` is `null` because we cannot reliably read the pending request from stdin during the error
path (the request may not have arrived yet, and reading stdin would block or require an
additional async task). JSON-RPC 2.0 §5 permits `null` for the response id when the request
id cannot be determined.

### Scope boundary

This task covers **connection-phase** failures only (before the bridge starts running). It does
NOT cover mid-session broker crashes (daemon dies while `_run_bridge` is active); that is a
separate concern.

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Add `_send_broker_error()` helper; wrap connect phase in `run()` with try/except |
| `tests/unit/test_broker_proxy.py` | Add `TestBrokerProxyUnavailableError` with ≥4 tests |

## Implementation Plan

### 1. `proxy.py` — add `_send_broker_error()`

New private async method:

```python
async def _send_broker_error(self, reason: str) -> None:
    """Write a JSON-RPC -32001 error to stdout and flush."""
    import json
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32001, "message": f"Broker unavailable: {reason}"},
    }) + "\n"
    writer = self._stdout
    if writer is None:
        writer = await self._make_stdout_writer()
    writer.write(payload.encode())
    try:
        await writer.drain()
    except Exception:
        pass
```

### 2. `proxy.py` — modify `run()`

Wrap the connect phase:

```python
async def run(self) -> None:
    try:
        if self._auto_spawn:
            await self._spawn_broker_if_needed()
        sock_reader, sock_writer = await self._connect_with_timeout()
    except Exception as exc:
        reason = str(exc)
        logger.error("Broker unavailable: %s", reason)
        await self._send_broker_error(reason)
        return
    # ... rest unchanged ...
```

### 3. `test_broker_proxy.py` — add `TestBrokerProxyUnavailableError`

Tests:
- `test_connect_timeout_sends_jsonrpc_error` — TimeoutError from `_connect_with_timeout` → error written to stdout writer
- `test_error_code_is_minus_32001` — error code in payload is -32001
- `test_error_message_includes_reason` — `"Broker unavailable:"` prefix present in message
- `test_run_does_not_raise_on_connect_failure` — `run()` returns without re-raising on TimeoutError
- `test_spawn_failure_sends_jsonrpc_error` — TimeoutError from `_spawn_broker_if_needed` → error written

## Acceptance Criteria

- [ ] Connection timeout produces a JSON-RPC `-32001` error response written to stdout
- [ ] Error message includes a human-readable reason (timeout, refused, stale socket)
- [ ] `run()` returns without re-raising — client does not hang indefinitely
- [ ] All existing broker tests pass
- [ ] `pytest --cov` coverage ≥ 90%
- [ ] `ruff check src/` passes
- [ ] `ruff format --check src/ tests/` passes

## Dependencies

- None (P2-T2 already handles stale socket recovery in spawn; this task is a pure error-surface improvement)

## Risk

Low. The change is additive — existing happy path is unchanged. The error path only activates
when connection already fails.
