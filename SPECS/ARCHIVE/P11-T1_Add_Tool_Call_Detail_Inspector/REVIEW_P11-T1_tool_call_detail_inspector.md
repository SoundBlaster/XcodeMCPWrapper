## REVIEW REPORT — P11-T1 Tool Call Detail Inspector

**Scope:** origin/main..HEAD
**Files:** 9 source/test files changed (531 insertions, 22 deletions)
**Date:** 2026-02-15

---

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

**Overall:** The implementation is correct, well-tested, and fully feature-flagged. A few low-severity observations below; none are blockers.

---

### Critical Issues

_None._

---

### Secondary Issues

**[Low] `_truncate_payload` double-serialises on every `log()` call**
- `_truncate_payload` calls `json.dumps` to measure size. For small payloads (the common case when `capture_payload=True`) this is a second serialisation on top of the file-write path. Impact is negligible for typical payloads but could be noticeable under high throughput.
- **Suggestion:** Use `sys.getsizeof` as a quick upper-bound fast-path, or compare against the limit only once in the hot path with a length estimate. Not worth addressing now; log if observed in profiling.

**[Low] `_truncate_payload` may split a multi-byte UTF-8 character at the byte boundary**
- The slice `encoded[:MAX_PAYLOAD_BYTES]` could split a multi-byte UTF-8 sequence. `errors="replace"` handles the decode correctly (replacing the broken sequence with U+FFFD), so the result is always valid UTF-8, but the `raw` string may end with a replacement character.
- **Verdict:** Acceptable; the replacement character signals truncation clearly and the resulting JSON is valid.

**[Low] Frontend `escapeHtml` is a minimal implementation**
- The function replaces `&`, `<`, `>`, `"` but not `'`. For JSON values rendered inside `<pre>`, this is sufficient (no attribute context), but a library function would be more complete.
- **Verdict:** Fine for the current use case inside `<pre>` elements.

**[Nit] Route ordering in `server.py` — verified non-issue**
- `GET /api/audit/{request_id}/detail` is registered before `GET /api/audit/export/json`. Verified via test: FastAPI correctly distinguishes these because the trailing path segments differ (`/detail` vs `/json` vs `/csv`). No shadowing occurs. No action needed.

---

### Architectural Notes

- The in-memory `OrderedDict` ring buffer is consistent with the existing in-memory `_entries` list pattern. No persistence is needed for payloads; the "last 500" semantics match a debugging use case well.
- Keeping `capture_payload` off by default is the right privacy choice.
- The `_FakeWebUIConfig` stub in `test_main.py` is a maintenance hazard — it needs to be updated every time a new config property is added. Worth considering a refactor to use `spec=WebUIConfig` in a `MagicMock` or subclass the real `WebUIConfig`. This is pre-existing tech debt, not introduced by this task.

---

### Tests

- 9 new tests in `TestPayloadCapture` covering: disabled-by-default, stores entry, missing request_id, truncation, ring buffer eviction (exact boundary), None payloads, disabled get_payload, and `_truncate_payload` static method.
- 4 new tests in `TestAuditDetailEndpoint` covering: 200 with payload, 404 capture disabled, 404 unknown ID, None payloads.
- Coverage held at **96.2%** (webui is excluded from coverage config by design).

---

### Next Steps

1. Consider refactoring `_FakeWebUIConfig` in `test_main.py` to use `MagicMock(spec=WebUIConfig)` to avoid future breakage when new config properties are added (pre-existing tech debt, low urgency).
2. Monitor `_truncate_payload` CPU cost under high-throughput scenarios if `capture_payload` is enabled in production.
