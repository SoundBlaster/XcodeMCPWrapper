# PRD: P14-T1 — Bound per-session ID restore maps in broker transport

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Dependencies:** FU-P13-T11 (✅), FU-P13-T15 (✅)

---

## 1. Objective

Prevent unbounded growth of per-session ID alias/restore structures in broker
transport while preserving JSON-RPC ID round-trip fidelity for both integer and
string request IDs.

---

## 2. Problem Summary

`ClientSession` currently keeps three mapping structures:
- `id_restore` (`local_alias -> original_id`)
- `string_id_map` (`original_string_id -> local_alias`)
- `int_id_map` (`original_int_id -> local_alias`)

These entries are added when requests are remapped but are not removed after a
response is routed or pending requests are drained. In long-lived broker
sessions this causes steady memory growth.

Additionally, local alias allocation wraps at 20-bit bounds without checking for
active aliases, so a wrapped allocation can collide with still-active mappings.

---

## 3. Design

### 3.1 Lifecycle cleanup for completed requests

Add explicit alias-release logic that:
- Removes `local_alias` from `id_restore`.
- Removes the corresponding entry from `string_id_map` / `int_id_map` only if
  that map still points to the same alias.

Invoke this cleanup when:
- Upstream responses are routed successfully.
- Pending requests are drained during shutdown.
- A request fails before reaching upstream (upstream unavailable or write
  failure).

### 3.2 Safe wrap behavior for local ID allocation

Update local alias allocator to skip aliases currently present in `id_restore`.
If all aliases are exhausted, raise a deterministic error and return `-32001`
to the client instead of reusing an active alias.

### 3.3 Behavior guarantees

- ID round-trip restoration remains exact for int and string IDs.
- Map size is bounded by active in-flight requests rather than historical
  traffic volume.
- Wrap-around never overwrites active alias mappings.

---

## 4. Files To Change

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/transport.py` | Add alias-release helpers, wrap-safe allocator, and cleanup calls on response/drain/error paths |
| `tests/unit/test_broker_transport.py` | Add regression tests for map pruning, bounded growth, and wrap-safe alias allocation |
| `SPECS/INPROGRESS/P14-T1_Validation_Report.md` | Capture gate results and acceptance evidence |

---

## 5. Acceptance Criteria

- [ ] Per-session restore/alias maps do not grow unbounded for completed requests.
- [ ] Existing ID round-trip fidelity guarantees remain intact for int and string IDs.
- [ ] Tests cover wrap/prune behavior and pass in CI.
- [ ] Quality gates are executed and documented.

