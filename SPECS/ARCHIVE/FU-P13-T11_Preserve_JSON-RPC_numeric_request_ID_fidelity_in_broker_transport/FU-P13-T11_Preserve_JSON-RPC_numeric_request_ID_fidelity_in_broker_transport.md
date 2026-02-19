# PRD: FU-P13-T11 — Preserve JSON-RPC numeric request ID fidelity in broker transport

**Task ID:** FU-P13-T11
**Phase:** Phase 13 Follow-up
**Priority:** P1
**Status:** IN PROGRESS
**Created:** 2026-02-19

---

## 1. Problem Statement

`UnixSocketServer._process_client_line` in `broker/transport.py` remaps integer request IDs using a lossy 20-bit bitmask:

```python
int_id = original_id & _ID_MASK   # _ID_MASK = 0xFFFFF (20 bits)
```

This causes three correctness failures:

1. **Truncation**: IDs larger than 1,048,575 (2^20 − 1) silently lose upper bits.
2. **Aliasing**: Two distinct IDs whose lower 20 bits match produce the same `broker_id`, routing responses to the wrong pending future.
3. **Negative IDs**: Python's `& 0xFFFFF` on a negative int produces a positive value, making restoration impossible.

The response restoration path compounds the problem by performing an O(n) linear scan of `string_id_map` to look up the original string ID and falling back to the truncated `int_local_id` for integers — an asymmetry that masks the bug in small-scale testing.

---

## 2. Deliverables

| Artifact | Description |
|----------|-------------|
| `src/mcpbridge_wrapper/broker/types.py` | Add `int_id_map`, `id_restore`, `_next_local_id` fields to `ClientSession` |
| `src/mcpbridge_wrapper/broker/transport.py` | Replace lossy mask with reversible per-session counter; O(1) restore; update docstring |
| `tests/unit/test_broker_transport.py` | Update broken tests; add large/negative/concurrent ID tests |

---

## 3. Design

### 3.1 New `ClientSession` fields

```python
# Forward maps: original_id → local_seq  (existing + new)
string_id_map: dict[str, int]       # kept for API compatibility
int_id_map: dict[int, int]          # NEW: original int → local_seq

# Reverse map: local_seq → original_id (NEW, O(1) restore)
id_restore: dict[int, int | str]

# Shared counter (NEW)
_next_local_id: int = 0             # field(default=0, repr=False)
```

A single `_next_local_id` counter is shared across string and integer allocations within a session, preventing cross-type collisions.

### 3.2 ID allocation helper

Add a module-level helper in `transport.py`:

```python
def _alloc_local_id(session: ClientSession) -> int:
    session._next_local_id += 1
    if session._next_local_id >= (1 << _SESSION_SHIFT):
        session._next_local_id = 1   # wrap (keeps within 20 bits)
    return session._next_local_id
```

### 3.3 Updated `_process_client_line` remapping

**String IDs** (extended to populate `id_restore`):
```python
if original_id not in session.string_id_map:
    local_int = _alloc_local_id(session)
    session.string_id_map[original_id] = local_int
    session.id_restore[local_int] = original_id
int_id = session.string_id_map[original_id]
```

**Integer IDs** (reversible mapping instead of bitmask):
```python
if original_id not in session.int_id_map:
    local_int = _alloc_local_id(session)
    session.int_id_map[original_id] = local_int
    session.id_restore[local_int] = original_id
int_id = session.int_id_map[original_id]
```

### 3.4 Updated response restoration (O(1))

Replace the O(n) scan in both `route_upstream_response` and `_drain_session`:

```python
int_local_id = broker_id & _ID_MASK
original_id: int | str = session.id_restore.get(int_local_id, int_local_id)
```

The fallback (`int_local_id`) handles legacy test fixtures that set `pending` directly without going through `_process_client_line`.

---

## 4. Test Plan (test-first)

### 4.1 Fix existing tests that break

| Test | Breakage | Fix |
|------|----------|-----|
| `test_integer_id_is_remapped` | Hardcodes `broker_id = (session_id << SHIFT) \| 10` | Check `10 in session.int_id_map`; derive `broker_id` dynamically |
| `test_string_id_restored_from_map` | Sets `string_id_map["req-abc"] = 5` but not `id_restore[5]` | Also set `s.id_restore[5] = "req-abc"` |
| `test_drain_with_string_id_sends_string_in_error` | Same as above | Also set `session.id_restore[3] = "my-req"` |

### 4.2 New tests

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_large_integer_id_round_trips` | Send integer ID `2**21` (> 20-bit) | Response restored with exact original ID |
| `test_negative_integer_id_round_trips` | Send integer ID `-1` | Response restored with `-1` |
| `test_concurrent_int_ids_no_collision` | Send IDs `1` and `1 + 2**20` in same session | Both have distinct `broker_id`s and are independently routable |
| `test_int_and_string_id_no_collision` | Send integer `1` then string ID that gets alias `1` | Counter ensures different local_ints; no aliasing |
| `test_integer_id_reuses_existing_mapping` | Send same integer ID twice | Same `broker_id` used both times (no double allocation) |

---

## 5. Acceptance Criteria

- [ ] Integer IDs (including negative and > 20-bit) are returned unchanged to clients
- [ ] Distinct concurrent numeric IDs cannot collide within a session
- [ ] Existing string-ID routing behavior remains backward compatible
- [ ] Broker transport tests cover ID round-trip fidelity for int and string IDs
- [ ] `pytest` passes (all tests green)
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes

---

## 6. Dependencies

- P13-T3 (UnixSocketServer implementation) ✅

---

## 7. Out of Scope

- Growing beyond 2^20 unique in-flight requests per session (counter wrap is acceptable)
- Persistence of session ID state across reconnects

---
**Archived:** 2026-02-19
**Verdict:** PASS
