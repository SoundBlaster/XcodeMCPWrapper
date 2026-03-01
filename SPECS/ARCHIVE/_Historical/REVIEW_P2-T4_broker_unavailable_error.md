## REVIEW REPORT — P2-T4: Broker unavailability JSON-RPC error

**Scope:** origin/main..HEAD
**Files:** 3 changed (proxy.py, test_broker_proxy.py, test_broker_stubs.py)
**Date:** 2026-03-01

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `except Exception` is broad in `run()`**

The connect-phase catch uses `except Exception`, which captures all non-`BaseException`
exceptions including unexpected ones (e.g., `MemoryError` is not an issue, but e.g., a
programming error in `_spawn_broker_if_needed` that raises `AttributeError` would be silently
swallowed). The guard prevents the client from hanging, so the trade-off is acceptable, but a
future refinement could narrow the catch to `(TimeoutError, OSError)` — the only exception
types that legitimately arise from the connect path.

**Suggested fix (optional):** Narrow to `except (TimeoutError, OSError)` with a fallback
`logger.exception` for anything else. Not a blocker; the current behaviour is safe.

**[Low] `id: null` in error response may confuse some clients**

JSON-RPC 2.0 §5 permits `null` for error responses when the request id is unknown. However,
some strict clients may log a warning or discard the response entirely if they cannot match it
to an outstanding request. Consider a future enhancement to read the pending request's `id`
from stdin with a short timeout (e.g., 0.5s) and use it in the error response. Not a blocker
for current acceptance criteria.

---

### Architectural Notes

- The `_send_broker_error` method is a clean, focused helper: <30 lines, single responsibility,
  reused for both spawn and connect failure paths.
- The inner guard in `_send_broker_error` (catching `_make_stdout_writer()` failure) is the
  right defensive posture — in non-pipe test environments the writer setup fails, and the guard
  ensures the error path doesn't itself raise.
- Existing tests that previously expected `run()` to raise `TimeoutError` have been correctly
  updated to verify the JSON-RPC error payload instead. The intent of those tests is preserved.

---

### Tests

- Added `TestBrokerProxyUnavailableError` (5 tests):
  - `test_connect_timeout_sends_jsonrpc_error` — full payload verification
  - `test_error_code_is_minus_32001` — code field check
  - `test_error_message_includes_reason` — prefix + exception text
  - `test_run_does_not_raise_on_connect_failure` — clean return
  - `test_spawn_failure_sends_jsonrpc_error` — spawn-phase error path
- Updated 2 existing tests (`test_broker_proxy.py` and `test_broker_stubs.py`) that previously
  expected `run()` to raise; now they verify the JSON-RPC error payload.
- Coverage: 91.59% (≥ 90% required). ✅
- All 732 tests pass, 5 skipped. ✅

---

### Next Steps

- **Optional FU:** Narrow `except Exception` to `(TimeoutError, OSError)` in `run()` for
  tighter exception scope. Low priority — current behaviour is safe and correct.
- **Optional FU:** Attempt to read the pending request's `id` from stdin with a short timeout,
  to use a real request id in the error response instead of `null`. Improves client
  compatibility. Low priority — JSON-RPC 2.0 permits `null`.
- No documentation changes required (this is an internal error-handling improvement with no
  user-visible configuration surface).

**VERDICT: PASS — no blockers; two low-severity observations documented above.**
