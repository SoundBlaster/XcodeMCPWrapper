## REVIEW REPORT — P4-T2: Broker Readiness Gate and tools/list Cache

**Scope:** origin/main..HEAD (commits 83aafe8..34c4a7a)
**Date:** 2026-03-06
**Verdict:** PASS — no actionable findings

---

## Summary of Changes

- `daemon.py`: Added `_BROKER_INIT_ID=0` / `_BROKER_TOOLS_ID=-1` constants; `_upstream_initialized` asyncio.Event; `_tools_list_cache` str|None; `upstream_initialized` property; `_send_broker_probes()` coroutine; intercept logic in `_read_upstream_loop()`; clear+probe on `_reconnect()`.
- `transport.py`: Replaced RECONNECTING polling while-loop with `asyncio.wait_for(asyncio.shield(event.wait()), timeout=queue_ttl)`; added cache hit path for `tools/list`.
- Tests: 5 new daemon tests (`TestBrokerReadinessGate`); 3 new transport tests (`TestToolsListCache`); 2 revised TTL/gate tests; 1 updated existing test.

---

## Review Checklist

### Correctness & Logic

- **Probe ID collision**: `_BROKER_INIT_ID=0` and `_BROKER_TOOLS_ID=-1` cannot collide with broker-assigned client IDs (`session_id << 20`, minimum 1_048_576). Correct.
- **Event lifecycle**: Cleared in `_reconnect()` before re-launch; set only after init probe response. Correct.
- **Cache lifecycle**: Cleared simultaneously with event in `_reconnect()`. Re-populated after tools probe response. Correct.
- **Gate semantics**: `asyncio.shield` ensures that a `wait_for` timeout cancels only the outer wait, not the underlying event — so concurrent waiters remain valid. Correct.
- **Cache hit path**: `cached_msg["id"] = raw_id` replaces broker probe ID with client's original ID. Returns immediately without touching alias maps (they were never allocated). Correct.
- **Non-result probe response**: Logged as warning; `_tools_list_cache` left as None (clients fall through to forwarding). Safe.

### Architecture & Design

- Reserved IDs documented at module level with justification. Good.
- Gate and cache are daemon-owned state, accessed by transport via public property. Clean boundary.
- `_BROKER_TOOLS_ID` probe is sent from the read loop (after init response) rather than a separate task — avoids race between stdin write and stdout read. Good design.

### Maintainability & Readability

- Docstrings on new methods and property are clear and reference related constants. Good.
- Inline comments explain the `asyncio.shield` rationale. Good.

### Performance & Resource Usage

- Cache hit path avoids the upstream round-trip; ID alias allocation is skipped too. Net cost: one `json.loads` + one `json.dumps`. Negligible (<1ms).
- Event wait is non-polling (`asyncio.Event.wait()`). Good.

### Security & Safety

- No new user-controlled input paths introduced.
- Probe responses intercepted before transport routing — probe IDs never reach clients.

### Concurrency/State

- `_upstream_initialized` and `_tools_list_cache` are read from the transport coroutine and written from the daemon read loop — both run in the same event loop, so no locking is needed. Correct.
- `asyncio.shield` + `asyncio.wait_for` pattern is the canonical asyncio approach for bounded waits that don't cancel the underlying coroutine. Correct.

### Test Coverage

- 91.0% total coverage (≥90% required). ✓
- New test classes cover: probe sent, event set, cache populated, event cleared on reconnect, noop when no upstream, cache hit (int ID), cache hit (string ID), cache miss.
- TTL timeout and gate-success paths both covered.

---

## Findings

None — no blockers, no high-severity issues, no nits worth addressing.

---

## Verdict: PASS
