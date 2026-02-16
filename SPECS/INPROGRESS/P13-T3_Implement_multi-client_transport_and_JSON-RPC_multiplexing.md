# PRD: P13-T3 — Implement multi-client transport and JSON-RPC multiplexing

**Version:** 1.0.0
**Status:** In Progress
**Branch:** `feature/P13-T3-multi-client-transport`
**Date:** 2026-02-17

---

## 1. Overview

Replace the stub `UnixSocketServer` in `src/mcpbridge_wrapper/broker/transport.py`
with a fully functional implementation that:

1. Binds to the Unix domain socket configured in `BrokerConfig.socket_path`.
2. Accepts concurrent client connections, each assigned a `ClientSession`.
3. Remaps JSON-RPC request IDs to prevent collisions across clients.
4. Forwards remapped requests to the `BrokerDaemon` upstream subprocess.
5. Routes upstream responses back to the originating client session.
6. Broadcasts JSON-RPC notifications (`id == null`) to all connected clients.
7. Handles malformed payloads from a single client without affecting others.
8. Enforces queue TTL and graceful-shutdown semantics per `BrokerConfig`.

---

## 2. Background

`BrokerDaemon` (P13-T2) owns the upstream `xcrun mcpbridge` subprocess and
exposes `_upstream` (an `asyncio.subprocess.Process`). Its `_read_upstream_loop`
currently parses lines but does not route them — it logs them and discards.

`UnixSocketServer` was scaffolded in P13-T1 with two stub methods
(`start` / `stop`). P13-T3 must fill in the complete implementation.

---

## 3. Architecture

### 3.1 Request ID Remapping

Outgoing IDs are namespaced to avoid collisions:

```
broker_id = (session_id << 20) | (original_id_int & 0xFFFFF)
```

- `session_id` occupies the upper 44 bits of a 64-bit integer.
- Original IDs are truncated to 20 bits within a session (overflow logged).
- String IDs are mapped to an integer alias stored in `ClientSession.string_id_map`.

On receiving a response from upstream:
```
client_id  = broker_id >> 20
original_id = broker_id & 0xFFFFF   (or looked up from string_id_map)
```

### 3.2 Notification Broadcast

Messages with `"id": null` (or no `id` field) from upstream are written to
all currently-connected `ClientSession` writers.

### 3.3 Error Isolation

When a client sends a malformed payload:
- Log the error.
- Respond to that client with a JSON-RPC parse error (`-32700`).
- Continue serving all other clients uninterrupted.

### 3.4 Queue TTL During Reconnection

When `BrokerDaemon` is in `RECONNECTING` state:
- New requests are held in a pending map.
- If `time.time() - queued_at > config.queue_ttl`, the request is rejected
  with JSON-RPC error code `-32001` ("Broker reconnecting").

### 3.5 Graceful Shutdown

`stop()` must:
1. Stop accepting new connections.
2. Complete in-flight requests or drain up to `graceful_shutdown_timeout`.
3. Write a JSON-RPC error to clients whose pending requests were not fulfilled.
4. Close all writer streams.

---

## 4. Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/transport.py` | Full implementation of `UnixSocketServer` |
| `src/mcpbridge_wrapper/broker/daemon.py` | Integrate `UnixSocketServer`: call `_route_upstream_response()` from `_read_upstream_loop` |
| `tests/unit/test_broker_transport.py` | New test file with ≥ 12 test cases |
| `tests/unit/test_broker_stubs.py` | Remove `NotImplementedError` assertions for `UnixSocketServer` |
| `SPECS/INPROGRESS/P13-T3_Validation_Report.md` | Quality gates and test coverage |

---

## 5. Acceptance Criteria

- [ ] At least two concurrent clients can perform tool calls successfully (tested with two asyncio streams)
- [ ] Responses are routed back to the correct client/request (verified by ID remapping tests)
- [ ] Broker handles malformed client payloads without affecting other clients (isolated error test)
- [ ] Queue/timeout behavior is tested and deterministic (TTL expiry and reconnect-queue tests)
- [ ] `ruff check src/` — zero issues
- [ ] `mypy src/` — no new type errors
- [ ] `pytest --cov` — coverage ≥ 90%

---

## 6. Dependencies

- P13-T2 ✅ — `BrokerDaemon` with upstream subprocess and `_read_upstream_loop`
- No external packages required (stdlib `asyncio` only)

---

## 7. Non-Goals

- P13-T4 (BrokerProxy / stdio forwarding) is out of scope for this task.
- No authentication beyond same-host-only socket (no `getpeereid` enforcement in P13-T3).
- No TLS or network transport — Unix socket only.
