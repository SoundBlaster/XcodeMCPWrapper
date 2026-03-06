# BUG-T9: Fix broker daemon not sending notifications/initialized before tools/list probe

**Status:** In Progress
**Priority:** P0
**Dependencies:** P4-T2
**Branch:** `fix/broker-missing-notifications-initialized`

---

## Problem Statement

After the broker's own `initialize` probe succeeds, `_read_upstream_loop` immediately sends a
`tools/list` probe (id=-1) without first sending the `notifications/initialized` notification.

According to the MCP specification, the client must send `notifications/initialized` after
receiving the server's `initialize` response to signal that the initialization phase is complete.
xcrun mcpbridge enforces this: it queues all non-handshake requests until the notification arrives.

**Consequence:**
- `tools/list` probe is queued indefinitely inside xcrun mcpbridge
- `_read_upstream_loop` blocks forever on `readline()` waiting for the tools/list response
- Real client `initialize` requests forwarded to upstream are also queued behind tools/list
- All client sockets time out; the broker appears unresponsive

**Confirmed via tracing:**
1. `TRACE: _upstream_initialized.SET!` — init probe response received correctly
2. `TRACE: before readline` — read loop blocks here, never advances
3. `TRACE_TRANSPORT: _handle_client CALLED` + `upstream_initialized.is_set=True` — client accepted, gate passed
4. Client test: `FAIL: timed out waiting for response` — no data ever written back

**Direct verification:**
```python
# Without notifications/initialized → tools/list: NO RESPONSE in 8s
# With notifications/initialized    → tools/list: responds immediately
```

---

## Root Cause

In `BrokerDaemon._read_upstream_loop` (`daemon.py`), after intercepting the init probe response
(`raw_id == _BROKER_INIT_ID`), the code:

1. Sets `_upstream_initialized` ✓
2. Sends `tools/list` probe ✗ (missing `notifications/initialized` before this)

The MCP handshake sequence must be:
```
client → initialize        (request, id=0)
server ← initialize result (response, id=0)
client → notifications/initialized  ← MISSING
client → tools/list        (request, id=-1)
server ← tools/list result (response, id=-1)
```

---

## Fix

In `_read_upstream_loop`, after receiving the init probe ack and before sending `tools/list`:

```python
# Complete the MCP handshake: send notifications/initialized so
# the upstream considers the session fully open before we issue
# any further requests.
initialized_notif = json.dumps(
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    separators=(",", ":"),
)
upstream.stdin.write((initialized_notif + "\n").encode())
await upstream.stdin.drain()
```

This applies to both initial startup and the reconnect path (reconnect calls `_send_broker_probes`
again; the same `_read_upstream_loop` handles the new probe response).

---

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Send `notifications/initialized` after init probe ack, before `tools/list` probe |
| `tests/unit/test_broker_daemon.py` | Update `test_tools_list_probe_sent_after_init_probe_acked` to assert ordering |

---

## Acceptance Criteria

- [ ] `notifications/initialized` notification written to upstream stdin immediately after init probe ack
- [ ] `notifications/initialized` appears before the `tools/list` probe in the written message sequence
- [ ] `tools/list` probe response received and cached (`_tools_list_cache` populated)
- [ ] Client `initialize` → `notifications/initialized` → `tools/list` round-trip succeeds end-to-end via broker socket
- [ ] All 785 tests pass with no regressions
- [ ] `ruff check src/` clean
- [ ] `mypy src/` clean
- [ ] Coverage ≥ 90%
