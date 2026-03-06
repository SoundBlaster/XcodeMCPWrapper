# P4-T2 — Cache tools/list in broker and gate client responses on upstream readiness

**Task ID:** P4-T2
**Priority:** P1
**Phase:** Phase 4: Broker Advanced Features
**Status:** Completed

## Problem

The broker forwards every client request directly to the upstream with no buffering. When the
upstream (`xcrun mcpbridge`) is blocked waiting for Xcode approval:

1. Client's `tools/list` reaches upstream → upstream blocked → no response
2. Upstream cycles (EOF) during the approval dialog (observed in logs: `Upstream EOF detected`)
3. Broker reconnects; the client's pending `tools/list` is now orphaned
4. Client (Zed, Cursor) caches the empty/no-response as "0 tools" indefinitely

The fix has two parts: **(A)** an upstream readiness gate that prevents clients from receiving
empty responses while the upstream is still initializing, and **(B)** a `tools/list` response
cache that serves clients instantly from memory once the upstream is truly ready.

## Architecture

### Reserved Broker-Internal IDs

JSON-RPC IDs used by the broker's own probes — never collide with client request IDs because
valid broker_ids are always `session_id << 20` and session IDs start at 1, so the minimum
broker_id is `1 << 20 = 1_048_576`:

```python
_BROKER_INIT_ID = 0    # initialize probe
_BROKER_TOOLS_ID = -1  # tools/list cache fetch
```

### Part A — Upstream Readiness Gate

**In `daemon.py`:**

1. Add `upstream_initialized: asyncio.Event` property (backed by `_upstream_initialized`).
   - Cleared in `__init__()` and at the start of each `_reconnect()` attempt.
   - Set after the broker's own `initialize` response is received from upstream.

2. New `_send_broker_probes()` coroutine:
   - Sends `{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":
     "2024-11-05","capabilities":{},"clientInfo":{"name":"mcpbridge-broker","version":"..."}}}`
     to upstream stdin.
   - Called immediately after `_launch_upstream()` in both `start()` and `_reconnect()`.

3. In `_read_upstream_loop()`, before routing each response to the transport:
   - If `msg.get("id") == _BROKER_INIT_ID` (i.e., 0):
     - Set `_upstream_initialized`.
     - Send `{"jsonrpc":"2.0","id":-1,"method":"tools/list","params":{}}` to upstream.
     - `continue` (do not route to transport).
   - If `msg.get("id") == _BROKER_TOOLS_ID` (i.e., -1):
     - Store result in `_tools_list_cache` (JSON string).
     - `continue` (do not route to transport).

**In `transport.py` (`_process_client_line`):**

Replace the existing `BrokerState.RECONNECTING` check with an `_upstream_initialized` gate
that covers both initial startup and reconnect scenarios:

```python
if not is_notification:
    if not self._daemon._upstream_initialized.is_set():
        try:
            await asyncio.wait_for(
                asyncio.shield(self._daemon._upstream_initialized.wait()),
                timeout=self._config.queue_ttl,
            )
        except asyncio.TimeoutError:
            await self._send_error(session, raw_id, -32001, "Upstream not ready — request TTL exceeded")
            if broker_id is not None:
                session.pending.pop(broker_id, None)
            if local_alias is not None:
                _release_local_alias(session, local_alias)
            return
```

### Part B — tools/list Cache

**In `transport.py` (`_process_client_line`):**

After the readiness gate, before remapping and forwarding:

```python
if method_name == "tools/list" and self._daemon._tools_list_cache is not None:
    cached = json.loads(self._daemon._tools_list_cache)
    cached["id"] = raw_id  # restore client's original ID
    await self._write_to_session(session, json.dumps(cached, separators=(",", ":")))
    # Release the alias since we're not forwarding to upstream
    if local_alias is not None:
        session.id_restore.pop(local_alias, None)
        if isinstance(raw_id, str):
            session.string_id_map.pop(raw_id, None)
        elif isinstance(raw_id, int):
            session.int_id_map.pop(raw_id, None)
        session.pending.pop(broker_id, None)
    return
```

**Cache invalidation:**
- `_tools_list_cache = None` at start of `_reconnect()`, before `_upstream_initialized.clear()`.
- New cache populated after reconnect via the `_BROKER_TOOLS_ID` probe response.

## Key Invariants

1. `_upstream_initialized` is set IFF the broker has received a valid `initialize` response
   from the current upstream process (not a past process).
2. `_tools_list_cache` holds the most recent `tools/list` result, or `None` if the cache has
   been invalidated by an upstream reconnect.
3. `_BROKER_INIT_ID = 0` and `_BROKER_TOOLS_ID = -1` are never exposed to clients; they are
   intercepted and dropped in `_read_upstream_loop` before reaching the transport router.
4. The readiness gate (`asyncio.wait_for` on `_upstream_initialized`) uses `asyncio.shield`
   so that the outer `wait_for` timeout does not cancel the event itself (only the wait).

## Deliverables

| File | Changes |
|------|---------|
| `src/mcpbridge_wrapper/broker/daemon.py` | `_upstream_initialized` event, `_tools_list_cache`, `_send_broker_probes()`, intercept in `_read_upstream_loop`, clear in `_reconnect()` |
| `src/mcpbridge_wrapper/broker/transport.py` | Replace RECONNECTING check with `_upstream_initialized` gate; add `tools/list` cache hit path |
| `tests/unit/test_broker_daemon.py` | Tests for readiness gate: probe sent after launch, event set on response, event cleared on reconnect, cache populated/invalidated |
| `tests/unit/test_broker_transport.py` | Tests for cache hit path, gate timeout, gate success, cache invalidation served correctly |

## Acceptance Criteria

- [ ] Broker sends `initialize` probe (id=0) to upstream immediately after `_launch_upstream()`
- [ ] `_upstream_initialized` event is set only after the probe response is received
- [ ] `_upstream_initialized` is cleared at the start of each reconnect attempt
- [ ] Client `tools/list` request is served from `_tools_list_cache` if cache is populated
- [ ] `_tools_list_cache` is cleared on upstream EOF/reconnect and refreshed after re-init
- [ ] Client requests with `is_notification=False` are gated on `_upstream_initialized` with TTL
- [ ] TTL expiry returns JSON-RPC error -32001 to the client (not an empty response)
- [ ] All existing quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, coverage ≥ 90%

## Out of Scope

- Documentation updates for P4-T2 behavior (can be done in a follow-up P1 doc task)
- Partial-results caching (e.g., caching `resources/list`)
- Distributed cache across multiple broker instances
