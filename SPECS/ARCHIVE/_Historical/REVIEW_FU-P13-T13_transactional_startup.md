# Review: FU-P13-T13 — Make broker startup transactional when transport bind/start fails

**Date:** 2026-02-19
**Verdict:** Approve

---

## Summary

The implementation correctly wraps all post-`_launch_upstream()` steps in a `try/except`
block that calls `_rollback_startup()` on any exception and re-raises, making `start()`
fully transactional. `self._state = BrokerState.READY` is now only reached when all steps
succeed. The `_rollback_startup()` method is idempotent and safe to call even when the
upstream was never launched. Six new unit tests cover all rollback scenarios and all pass.

---

## Issues Found

### Low: `_stopped_event` not set after rollback

**Location:** `daemon.py:_rollback_startup()`

`_rollback_startup()` leaves `_stopped_event` unset. If a caller somehow awaits
`_stopped_event` after a failed `start()`, it would block indefinitely.

In practice this is not reachable: `run_forever()` calls `await self.start()` and
propagates the exception before ever waiting on `_stopped_event`. `stop()` short-circuits
on `state == STOPPED`. So this is not a bug in any exercised code path.

**Recommendation:** Add `self._stopped_event.set()` in `_rollback_startup()` to make the
method consistent with `stop()` and guard against future callers.

---

### Low: `_stop_event` remains cleared after rollback

**Location:** `daemon.py:start()` → `daemon.py:_rollback_startup()`

`start()` calls `self._stop_event.clear()` before starting the read task. After a rollback,
`_stop_event` is left cleared (not set). This means `run_forever()` would block on
`await self._stop_event.wait()` if it somehow reached that line after a failed start —
which it cannot, since the exception propagates first.

Same non-issue as above, but worth noting for completeness.

**Recommendation:** Add `self._stop_event.set()` in `_rollback_startup()` for defensive
completeness. It costs nothing and makes the event states consistent with STOPPED.

---

### Nit: rollback log message doesn't include exception context

**Location:** `daemon.py:_rollback_startup()` line ~237

```python
logger.warning("Rolling back failed broker startup.")
```

The warning doesn't include the cause. A caller catching the re-raised exception can log it,
but having the cause in the rollback log would make log triage easier when debugging broker
startup failures in production.

**Recommendation:** Pass `exc_info=True` or the exception string if called from an
`except` block — but since `_rollback_startup` doesn't receive the exception, this would
require restructuring. Low priority; leave as-is or document in the method docstring.

---

### Nit: inconsistency between `stop()` and `_rollback_startup()` upstream termination

**Location:** `daemon.py:stop()` vs `daemon.py:_rollback_startup()`

`stop()` closes `upstream.stdin` before waiting for the subprocess. `_rollback_startup()`
does not. In a rollback scenario, the upstream process hasn't yet received any MCP requests
(transport hasn't started), so this difference is harmless in practice. Still, a uniform
termination sequence would be more maintainable.

**Recommendation:** Low priority; acceptable as-is given the different contexts.

---

## Positive Observations

- The `try/except` boundary is correctly drawn — only post-`_launch_upstream()` steps are
  inside, since `_launch_upstream()` failure itself requires no rollback.
- The re-raise (`raise`) without argument preserves the original exception and traceback.
- `_rollback_startup()` sets `self._upstream = None` after termination, ensuring
  subsequent calls are safe.
- `_cleanup_files()` uses `missing_ok=True` internally, so calling it when no files exist
  is safe.
- Tests use `patch.object(type(cfg.pid_file), "write_text", ...)` to patch PosixPath's
  class-level method, correctly working around the read-only instance attribute constraint.
- All 6 new tests pass; the full suite (559 tests) remains green.

---

## Follow-up Tasks

None required for correctness. Optional defensive improvements:

- **FU-P13-T13-FU-1** (Low): Set `_stopped_event` and `_stop_event` in `_rollback_startup()`
  for defensive consistency with the STOPPED state contract.
