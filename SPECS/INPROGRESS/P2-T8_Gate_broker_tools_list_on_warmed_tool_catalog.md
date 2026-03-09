# P2-T8: Gate broker tools/list on warmed tool catalog

**Status:** In Progress
**Priority:** P0
**Dependencies:** BUG-T9, P4-T2
**Branch:** `codex/p2-t8-broker-tools-catalog-gate`

---

## Problem Statement

Strict MCP clients such as Cursor and Zed cache the first successful `tools/list`
response they receive from a server. In broker mode, `mcpbridge-wrapper` currently
lets external client `tools/list` requests pass as soon as the upstream
`initialize` round-trip finishes.

That is too early.

The broker still has a second startup phase after `initialize`:

1. Send `notifications/initialized` to `xcrun mcpbridge`
2. Probe `tools/list` internally
3. Cache the resulting tool catalog for later clients

If an external client sends `tools/list` during that warm-up gap, it can observe an
empty or invalid tools list and cache that broken success locally. The user then
sees a green MCP indicator but fewer than the full 20 Xcode tools until they toggle
the server multiple times.

---

## Root Cause

In `UnixSocketServer._process_client_line`, the only readiness gate for all
request/response traffic is `daemon.upstream_initialized`. That event becomes set
immediately after the broker receives the upstream `initialize` response.

At that moment, however:

- the broker's internal `tools/list` probe may still be in flight
- `_tools_list_cache` may still be `None`
- the upstream may still return an empty or malformed tools payload during cold-start

Because `tools/list` follows the same gate as every other method, the first client
tool-discovery request can race ahead of the broker's own cache warm-up.

---

## Fix

Introduce a second broker readiness concept dedicated to tool discovery:

- add a `tools_catalog_ready` event on the daemon
- set it only after the broker receives a non-empty, structurally valid
  `tools/list` probe result
- clear it on reconnect or when the internal probe returns an empty/invalid catalog
- make external client `tools/list` wait on `tools_catalog_ready` instead of only
  `upstream_initialized`

This preserves existing behavior for non-`tools/list` methods while making the
first tool-discovery handshake safe for strict clients.

---

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Add explicit tools-catalog readiness event and reject empty/invalid warm-up results |
| `src/mcpbridge_wrapper/broker/transport.py` | Hold client `tools/list` until broker tool catalog is ready |
| `tests/unit/test_broker_daemon.py` | Cover ready/non-ready broker tool catalog transitions |
| `tests/unit/test_broker_transport.py` | Cover client `tools/list` wait/error/cache paths |
| `tests/integration/test_broker_multi_client.py` | Keep integration coverage aligned with the stronger broker contract |

---

## Acceptance Criteria

- [ ] Broker does not forward external `tools/list` while the internal tools cache is still cold
- [ ] Empty or invalid internal `tools/list` probe results do not open the client-facing readiness gate
- [ ] Client `tools/list` returns either a warmed catalog or a clear TTL error, never a premature empty success
- [ ] Existing non-`tools/list` broker traffic still flows after `upstream_initialized`
- [ ] `pytest` passes
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes
- [ ] `pytest --cov` remains at or above 90%
