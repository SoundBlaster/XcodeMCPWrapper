# REVIEW: BUG-T9 — Fix broker daemon not sending notifications/initialized before tools/list probe

**Date:** 2026-03-06
**Reviewer:** Claude (automated)
**Verdict:** PASS — no actionable findings

---

## Summary

BUG-T9 correctly identifies and fixes the missing `notifications/initialized` notification in the
broker's MCP handshake sequence. The fix is minimal, targeted, and verified both by unit tests and
live end-to-end testing against xcrun mcpbridge.

---

## Code Review

### `src/mcpbridge_wrapper/broker/daemon.py`

**Change:** 15 lines added in `_read_upstream_loop` after the init probe ack intercept.

- The `notifications/initialized` notification is written immediately after `_upstream_initialized.set()`, before the `tools/list` probe — correct ordering per MCP spec.
- Exception handling matches the existing `tools/list` probe pattern (log warning, continue).
- The fix applies to both initial startup and reconnect paths (reconnect reuses the same `_read_upstream_loop`, which intercepts the new upstream's probe response the same way).
- No changes to public interfaces, no new state introduced.

**Assessment:** Correct, minimal, consistent with existing style. ✅

### `tests/unit/test_broker_daemon.py`

**Change:** `test_tools_list_probe_sent_after_init_probe_acked` strengthened from `>= 2` writes to `>= 3`, with two new assertions:
1. `notifications/initialized` is present in written messages.
2. `notifications/initialized` index < `tools/list` probe index (ordering enforced).

**Assessment:** Assertions are precise and catch both presence and ordering. ✅

---

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest` (785 tests) | ✅ PASS |
| `ruff check src/` | ✅ PASS |
| `mypy src/` | ✅ PASS |
| Coverage | ✅ 90.8% |

---

## Root Cause Analysis Quality

The root cause investigation was thorough:
- Added TRACE prints to both `daemon.py` and `transport.py` in the uvx cache to isolate the exact failure point.
- Confirmed `_upstream_initialized` IS set correctly (not the issue).
- Confirmed `_handle_client` IS called (not a socket issue).
- Confirmed `tools/list` never responds without `notifications/initialized`.
- Confirmed `tools/list` responds immediately WITH `notifications/initialized`.

No shortcuts or workarounds — fix addresses the actual protocol violation.

---

## Findings

None. No actionable issues identified.

---

## Follow-up Tasks

None required. FOLLOW-UP step skipped.
