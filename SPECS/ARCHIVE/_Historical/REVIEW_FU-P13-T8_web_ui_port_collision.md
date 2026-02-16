## REVIEW REPORT — FU-P13-T8: Web UI port collision hardening

**Scope:** origin/main..HEAD (commits b06468f..2da4d89)
**Files changed:** 2 (`webui/server.py`, `test_main_webui.py`)
**Date:** 2026-02-16

---

### Summary Verdict
- [x] Approve

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `except SystemExit` is broad — could mask unrelated `sys.exit()` calls**

The new `except SystemExit` in `run_server()` catches any `SystemExit` raised by
`uvicorn.run()`, including hypothetical future `sys.exit(0)` calls (clean shutdown).
In practice uvicorn only calls `sys.exit(1)` on bind failure, so this is safe.
If desired, the `except` could be narrowed to `except SystemExit as exc: if exc.code != 1: raise`
— but this is over-engineering for the current behavior.

Recommendation: Accept as-is; add a comment clarifying this if the code is revisited.

**[Nit] Test imports inside test method body**

`test_toctou_systemexit_from_uvicorn_does_not_crash_thread` performs several imports
inside the method body (`from mcpbridge_wrapper.webui.server import run_server`, etc.).
The pattern is consistent with other tests in the file, but top-level imports would be
cleaner for readability. Not a correctness issue.

Recommendation: Low-priority; leave consistent with existing style.

---

### Architectural Notes

- The `run_server()` function now has a complete exception surface: `OSError` (bind error surfaced
  directly) and `SystemExit` (uvicorn's internal handling of bind error). Both write to stderr and
  return cleanly, so the daemon thread lifecycle is fully deterministic.
- The TOCTOU window between `is_port_available()` and `uvicorn.run()` is now fully handled:
  pre-check prevents the common case; `SystemExit` catch handles the race.
- No changes to `__main__.py` were needed — the fix is entirely within `server.py`.

---

### Tests

- 42 tests in `test_main_webui.py` (was 41), all pass.
- 472 total tests pass, 5 skipped.
- Coverage: 95.6% (≥90% required).
- `PytestUnhandledThreadExceptionWarning` about port 8080 is resolved — no longer appears in CI.

---

### Next Steps

- No actionable follow-up items. FOLLOW-UP step is skipped per FLOW rules (no findings require
  new workplan tasks).
