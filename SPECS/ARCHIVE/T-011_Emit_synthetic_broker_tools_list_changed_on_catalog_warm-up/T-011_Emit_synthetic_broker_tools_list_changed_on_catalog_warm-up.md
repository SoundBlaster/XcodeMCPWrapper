# PRD: T-011 — Emit synthetic broker tools/list_changed on catalog warm-up

**Task ID:** T-011
**Priority:** P1
**Status:** Planned
**Date:** 2026-03-10
**Owner:** Codex

## Objective

Extend the broker so connected clients receive a synthetic
`notifications/tools/list_changed` when the broker's cached `tools/list` catalog first becomes
usable after Xcode approval, or when a later reconnect produces a materially different non-empty
catalog. The goal is to give strict MCP clients an explicit catalog-change hint even when
`xcrun mcpbridge` itself never emits that notification.

## Context

`T-010` established two relevant facts:

1. During pre-approval startup, the broker can remain alive while no usable `tools/list`
   response is yet available.
2. In a synchronized direct run against `xcrun mcpbridge`, Xcode approval surfaced readiness via
   a successful `tools/list` returning 20 tools, but no `notifications/tools/list_changed`
   arrived from upstream.

The broker already has the right warm-up mechanism: an internal `initialize` probe followed by
repeated internal `tools/list` probes with bounded backoff until a non-empty catalog is cached.
This task should reuse that mechanism rather than adding a second polling loop.

## Deliverables

1. Broker state changes in `src/mcpbridge_wrapper/broker/daemon.py`
2. Client-notification plumbing in `src/mcpbridge_wrapper/broker/transport.py`
3. Unit coverage in:
   - `tests/unit/test_broker_daemon.py`
   - `tests/unit/test_broker_transport.py`
4. Validation report:
   - `SPECS/INPROGRESS/T-011_Validation_Report.md`

## Success Criteria

1. When the broker cache transitions from cold/unavailable to a non-empty tool catalog, a single
   synthetic `notifications/tools/list_changed` is broadcast to connected clients.
2. Repeated empty retry probes do not emit notifications.
3. A reconnect that yields the same non-empty catalog does not emit duplicate change
   notifications.
4. A reconnect that yields a different non-empty catalog emits one new synthetic notification.
5. Existing `tools/list` readiness gating and cached-response behavior remain unchanged.

## Test-First Plan

Before changing runtime code, add or update tests that prove:

1. Warm-up success triggers exactly one synthetic catalog-change notification.
2. Empty or invalid probe results do not trigger it.
3. Reconnect with unchanged catalog is silent.
4. Reconnect with changed catalog re-triggers the notification.
5. Transport broadcast formatting matches a normal MCP notification shape and reaches all active
   sessions.

## Implementation Plan

### Phase 1: Broker state transition hook

- Inputs:
  - current probe handling in `BrokerDaemon._read_upstream_loop`
  - current cache fields `_tools_list_cache` and `_tools_catalog_ready`
- Outputs:
  - explicit helper for deciding whether a new cached catalog represents a meaningful change
  - one broker-side trigger point when synthetic notification should be emitted
- Verification:
  - targeted daemon unit tests for warm-up and reconnect transitions

### Phase 2: Transport broadcast path

- Inputs:
  - existing `UnixSocketServer._broadcast`
  - MCP notification shape for `notifications/tools/list_changed`
- Outputs:
  - transport helper to emit a synthetic notification to all sessions
  - no change to client request/response ID handling
- Verification:
  - transport unit tests asserting all clients receive the notification once

### Phase 3: Validation and operator notes

- Inputs:
  - full broker test suite results
  - manual or scripted observation notes where practical
- Outputs:
  - validation report capturing quality-gate results and observed client behavior
- Verification:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov`

## Decision Points

1. The notification should be synthetic only on broker-owned cache transitions, not on every
   upstream `tools/list` response.
2. Catalog comparison should be based on normalized cached payload content, not object identity.
3. The broker should not try to fabricate a new `tools/list` payload for clients; it should only
   emit the MCP change notification and let clients decide whether to refetch.

## Notes

If implementation confirms improved behavior in Cursor or Zed after approval, capture that in the
validation report and consider a short troubleshooting note follow-up only if the behavior becomes
user-visible enough to document.
