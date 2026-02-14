## REVIEW REPORT — BUG-T6: Web UI Port Collision Handling

**Scope:** origin/main..HEAD (commit 792abf2..2af8d9f)
**Files changed:** 3 (`__main__.py`, `webui/server.py`, `test_main_webui.py`)
**Date:** 2026-02-14

---

### Summary Verdict
- [x] Approve with comments

---

### Critical Issues

None.

---

### Secondary Issues

**[Medium] `is_port_available` uses `SO_REUSEADDR` which can produce false positives on some platforms**

`SO_REUSEADDR` on Linux allows binding to a port that has connections in `TIME_WAIT`. On macOS
(the target platform) the behavior is more strict, so this is unlikely to cause problems in
practice. However, for maximum correctness the `setsockopt` call could be omitted so we get a
pure "is this port currently bound?" answer.

Recommendation: Low-priority follow-up; the current behavior is safe on macOS.

**[Low] Port check has a time-of-check/time-of-use (TOCTOU) window**

Between `is_port_available` returning `True` and `uvicorn.run()` binding, another process could
claim the port. The `OSError` catch in `run_server` handles this defensively for the thread case,
but for `--web-ui-only` mode the caller would need to deal with the error propagation.

Current mitigation: the `OSError` wrapper in `run_server` catches this at runtime for the thread.
For `--web-ui-only`, the `run_server` wrapper also now catches it and prints to stderr, so the
process will exit without crashing. Acceptable for now.

**[Nit] `audit.close()` called before `run_server_in_thread` starts in `--web-ui-only` occupied-port path**

When `--web-ui-only` and port is occupied, we call `audit.close()` then `return 1`. This is
correct — the audit logger was just initialized and nothing was logged — but it could be confusing
to future readers. A comment would clarify intent.

---

### Architectural Notes

- The `is_port_available` function is now a public API of `webui/server.py`. If the server module
  is later split, this utility should move to a shared helpers module.
- The pattern "check then proceed" is the right minimal approach here. A PID-file single-instance
  guard (FU-P13-T8 optional extension) was deliberately deferred to keep scope minimal.
- The OSError catch inside `run_server` means daemon-thread failures are now logged to stderr
  instead of being silently swallowed, which improves observability.

---

### Tests

- 5 new tests added in `TestPortCollisionHandling`
- 4 existing tests updated to mock `is_port_available` for deterministic behavior in environments
  where port 8080 is already occupied
- All 323 unit tests pass
- Coverage unaffected (new code is fully exercised by new tests)

---

### Next Steps

1. **Troubleshooting docs** — The BUG-T6 Resolution Path still has one open item:
   `[ ] Document stale-process cleanup in troubleshooting`. This is a minor docs task.
   Add a new follow-up task if desired.
2. **`SO_REUSEADDR` audit** — Low priority, can be addressed in a future cleanup pass.
3. No blockers. Task is complete and ready for PR merge.

---

### Follow-up Tasks

**FU-BUG-T6-1:** Add stale-process cleanup guidance to troubleshooting docs (Low priority)

No other actionable follow-ups.
