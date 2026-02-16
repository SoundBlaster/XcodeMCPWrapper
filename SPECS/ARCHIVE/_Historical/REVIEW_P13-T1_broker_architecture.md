## REVIEW REPORT — P13-T1 Broker Architecture

**Scope:** origin/main..HEAD
**Files:** 11 (4 commits)
**Date:** 2026-02-16
**Reviewer:** Claude

---

### Summary Verdict

- [x] Approve with comments

---

### Critical Issues

None.

---

### Secondary Issues

**[Medium] ID remapping scheme may overflow for long-running sessions**

The PRD specifies `broker_id = (client_id << 20) | original_id_int`. If `original_id` is a positive integer that exceeds 2^20 (≈ 1M), the remapped ID could collide with a different client's requests. While this is extreme in practice for JSON-RPC IDs, the spec should either document the constraint explicitly (original int IDs must fit in 20 bits) or choose a wider bit-split.

Suggested fix: Document the 20-bit limit in `transport.py` and add a validation note. Alternatively, use a flat sequential `broker_id` counter (a simple monotonic int per broker session) with a `broker_id → (client_id, original_id)` lookup table — this eliminates the overflow concern entirely.

**[Low] `BrokerConfig.default()` uses `Path.home()` directly**

This will fail in minimal test environments that lack a real home directory. `pytest` on CI mocks won't affect it, but direct unit tests of the default path may produce unexpected paths. The existing tests don't test `Path.home()` behavior, so this is low-risk now but could matter in P13-T2 tests.

Suggested fix: Accept the current design for the stub. Add a note for P13-T2 to consider injecting `base_dir` via an env var (`MCP_BROKER_DIR`) as the existing `webui` modules do with `data_dir`.

**[Low] `ClientSession.pending` uses `int` keys only**

The `string_id_map` field correctly handles string IDs, but `ClientSession.pending` is typed as `dict[int, asyncio.Future]`. In P13-T3 when string ID support is added, the key type will need to be `int | str` or a string-to-int remapped scheme applied. Documenting this now prevents a silent type mismatch.

---

### Architectural Notes

1. **UDS over TCP was the right call.** Filesystem-permission security (mode 0600) eliminates a whole class of local network attack vectors without any token management overhead.

2. **Broadcast of `id == null` notifications is underspecified.** JSON-RPC 2.0 notifications (no `id` field) must be broadcast to all clients. The PRD mentions this but does not define what happens when one client's write buffer is full — should the broker drop the notification for that client, close that client, or block? This should be resolved in P13-T3 design.

3. **Reconnect behavior during client connection acceptance is a good design choice.** Queuing new client requests during RECONNECTING rather than rejecting them means brief upstream crashes are invisible to well-behaved clients. The 60s TTL is reasonable.

4. **Module scaffold structure is clean.** `types.py / daemon.py / transport.py / proxy.py` maps exactly to the four responsibility boundaries in the PRD, making it easy to assign P13-T2 through P13-T4 to the correct files.

---

### Tests

- **23 new tests** in `tests/unit/test_broker_stubs.py` covering all stub classes.
- Coverage: **96.06%** (up from baseline; broker stubs are 100% covered).
- `pytest-asyncio` is used for async stub tests — no issues with existing async test infrastructure.
- No mock of `Path.home()` in `test_default_factory` — acceptable for a design task but flagged for P13-T2.

---

### Next Steps

1. *(Actionable)* Document the 20-bit original ID constraint or switch to a flat broker_id counter in P13-T3 design. Add to P13-T3 planning notes.
2. *(Actionable)* Clarify broadcast notification drop policy for slow clients in P13-T3 spec.
3. *(Non-actionable now)* Consider `MCP_BROKER_DIR` env var override for socket/PID paths in P13-T2.
4. *(Non-actionable now)* Widen `ClientSession.pending` key type to `int | str` when implementing P13-T3.

---

### Follow-up Assessment

Two actionable items exist but both are design clarifications for P13-T3 (not blocking bugs):
1. ID remapping clarification / alternative scheme note
2. Broadcast drop policy for slow clients

These are low-risk design notes that can be incorporated into the P13-T3 planning PRD rather than creating separate follow-up tasks. **FOLLOW-UP is skipped** — items will be addressed organically in P13-T3 PLAN step.
