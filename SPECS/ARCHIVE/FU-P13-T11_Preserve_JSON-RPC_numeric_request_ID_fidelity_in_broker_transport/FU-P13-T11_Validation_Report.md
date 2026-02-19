# Validation Report: FU-P13-T11 — Preserve JSON-RPC numeric request ID fidelity in broker transport

**Date:** 2026-02-19
**Verdict:** PASS

---

## Changes Delivered

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/types.py` | Added `int_id_map`, `id_restore`, `_next_local_id` fields to `ClientSession` |
| `src/mcpbridge_wrapper/broker/transport.py` | Added `_alloc_local_id()` helper; replaced lossy `& _ID_MASK` bitmask with reversible per-session counter for integer IDs; replaced O(n) scan with O(1) `id_restore.get()` in `route_upstream_response` and `_drain_session`; updated module docstring |
| `tests/unit/test_broker_transport.py` | Fixed 3 existing tests; added 5 new `TestIntegerIDFidelity` tests |

---

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/unit/` | ✅ 526 passed, 9 skipped |
| `ruff check src/mcpbridge_wrapper/broker/` | ✅ All checks passed |
| `mypy src/mcpbridge_wrapper/broker/ --ignore-missing-imports` | ✅ Success: no issues found in 5 source files |

---

## Acceptance Criteria

- [x] Integer IDs (including negative and > 20-bit) are returned unchanged to clients
  - Verified by `test_large_integer_id_round_trips` (ID = 2^21) and `test_negative_integer_id_round_trips` (ID = -1)
- [x] Distinct concurrent numeric IDs cannot collide within a session
  - Verified by `test_concurrent_int_ids_no_collision` (IDs 1 and 1 + 2^20)
- [x] Existing string-ID routing behavior remains backward compatible
  - All existing string-ID tests pass; `string_id_map` field retained
- [x] Broker transport tests cover ID round-trip fidelity for int and string IDs
  - `TestIntegerIDFidelity` class added with 5 tests; `test_int_and_string_id_no_collision` covers cross-type safety

---

## Implementation Notes

- The `_alloc_local_id()` counter is **shared** across string and integer allocations, preventing cross-type collisions (e.g. integer `1` and a string ID cannot receive the same local alias).
- The `id_restore` reverse map enables O(1) restoration in both `route_upstream_response` and `_drain_session`, replacing the previous O(n) linear scans of `string_id_map`.
- The fallback in `id_restore.get(int_local_id, int_local_id)` preserves backward compatibility for legacy test fixtures that directly set `session.pending` without routing through `_process_client_line`.
- Counter wraps at `2^20 - 1` (skipping 0), preserving the 20-bit `broker_id` encoding invariant.
