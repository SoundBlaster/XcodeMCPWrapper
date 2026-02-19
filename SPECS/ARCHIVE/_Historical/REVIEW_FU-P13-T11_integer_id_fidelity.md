## REVIEW REPORT — FU-P13-T11: Preserve JSON-RPC numeric request ID fidelity in broker transport

**Scope:** commits 69d1fbc..adc9d7a (branch `claude/implement-flow-specs-Ry4XN`)
**Files:** 5 (types.py, transport.py, test_broker_transport.py, Workplan.md, INDEX.md + next.md)

---

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None. All correctness requirements from the task spec are met.

---

### Secondary Issues

**[Low] `# noqa: F821` comment left on `_alloc_local_id`**

`transport.py:52` has `def _alloc_local_id(session: ClientSession) -> int:  # noqa: F821` after ruff auto-fixed the type annotation. Since `ClientSession` is explicitly imported at the top of the module, `F821` (undefined name) can never fire here. The comment is harmless but misleading and should be removed in a future cleanup pass.

**[Low] `_next_local_id` field appears in `ClientSession.__init__` signature**

The field is declared as `field(default=0, repr=False)` which means `init=True` — callers can accidentally pass `_next_local_id=n` during construction. Using `field(default=0, init=False, repr=False)` would make it strictly internal. This is a minor API hygiene issue; the current form is still safe since tests don't exploit it.

---

### Architectural Notes

1. **Counter wrap**: `_alloc_local_id` wraps at `2^20 - 1` ≈ 1M IDs. A single MCP session sending > 1M distinct IDs would start recycling aliases. In practice this is not a concern for MCP workloads, but a session-level guard (e.g. capping `int_id_map` and `string_id_map`) would prevent memory growth for long-lived broker sessions. This is a separate concern from the bug fixed here.

2. **Fallback in `id_restore.get()`**: The fallback `int_local_id` silently returns an integer for any pending entry that bypassed `_process_client_line`. This is intentional to preserve compatibility with test fixtures that set `pending` directly, but it means a programming error (failing to go through the proper path) would silently produce a wrong ID in production. An explicit log warning at DEBUG level when the key is missing could aid future debugging.

3. **`string_id_map` kept for compatibility**: The existing `string_id_map` field is retained. It still serves as the forward map for string IDs, but the reverse lookup path now goes exclusively through `id_restore`. This creates mild redundancy (string IDs appear in both `string_id_map` and `id_restore`). A future cleanup could unify into a single forward map `id_map: dict[int | str, int]`.

---

### Tests

- 526 unit tests pass, 9 skipped — no regressions.
- 5 new tests in `TestIntegerIDFidelity` cover all stated acceptance criteria.
- `test_string_id_reuses_existing_alias` continues to pass, confirming backward compatibility for string IDs.
- The `test_drain_with_string_id_sends_string_in_error` test now explicitly populates `id_restore`, making the test setup more explicit and accurate.

---

### Next Steps

No blockers. The two Low findings can be addressed in a future cleanup task if desired:

- FU-P13-T11-1 (optional): Remove `# noqa: F821` comment from `_alloc_local_id` and change `_next_local_id` to `field(default=0, init=False, repr=False)`.

FOLLOW-UP is **not required** — the issues found are cosmetic/stylistic and do not affect correctness or safety.
