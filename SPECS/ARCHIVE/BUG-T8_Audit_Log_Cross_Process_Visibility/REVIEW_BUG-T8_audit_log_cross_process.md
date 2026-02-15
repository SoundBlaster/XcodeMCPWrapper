## REVIEW REPORT — BUG-T8: Audit Log Cross-Process Visibility

**Scope:** origin/main..HEAD
**Files:** 2 (audit.py +46 lines; test_audit.py +85 lines)
**Date:** 2026-02-15

---

### Summary Verdict
- [x] Approve

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `_load_history` reads the currently-open log file**
`_open_log_file()` creates a new `audit_YYYYMMDD_HHMMSS.jsonl` file and then `_load_history()` globs the directory and opens it for reading. Because the new file is empty at that point, reading it produces zero lines — so there is no double-read or data duplication, and the behavior is correct. However, if two processes start in the same second and both produce `audit_YYYYMMDD_HHMMSS.jsonl`, only one file actually exists (the second clobbers or appends). This is a pre-existing limitation of the filename scheme and not introduced by this PR.

**[Low] `_load_history` runs outside the lock**
`_load_history` is called from `__init__` before any other thread can hold `self._lock`, so there is no race in practice. The comment in the docstring could note this to prevent future callers from calling it mid-lifecycle unsafely.

**[Nit] Shadowing loop variable `line`**
Inside `_load_history`, `line` is both the outer loop variable (from `for line in raw_lines`) and reassigned by `line = line.strip()`. This is benign but slightly confusing; a local name like `stripped` would be cleaner.

---

### Architectural Notes

- The fix deliberately targets **startup visibility only** (Option A from the workplan). Live cross-process streaming remains out of scope until Phase 13 broker work clarifies the long-term architecture. This is the right call — over-engineering here would duplicate work Phase 13 will undo.
- The raw-line cap (`raw_lines[-_max_memory_entries:]`) is applied before JSON parsing, which is cheap and correct. It does mean a single file with 10 001 lines of garbage JSON would still occupy memory momentarily during the strip/parse loop, but this is negligible.
- The test `test_startup_respects_max_memory_entries` reaches into `audit_b._max_memory_entries` and `audit_b._entries` directly, bypassing the public API. Acceptable for a low-level unit test, but worth noting if the internals change.

---

### Tests

- 4 new tests in `TestStartupHistoryLoad` cover the key scenarios: basic cross-process load, cap enforcement, malformed-line skipping, and multi-file chronological order.
- All 28 audit tests pass; full suite 386 passed / 5 skipped.
- Coverage: 96.2% on main modules (webui/* excluded by pyproject.toml by policy).
- Ruff and mypy both clean.

---

### Next Steps

No blocking follow-up tasks. Optional low-priority improvements noted:
- Rename shadowed `line` variable to `stripped` (nit).
- Add docstring note that `_load_history` is init-only and must not be called after threads start.

These are nit-level and do not warrant a follow-up task.

**FOLLOW-UP: SKIPPED** — no actionable findings above nit level.
