# BUG-T8 Validation Report

**Task:** Audit log cross-process visibility
**Date:** 2026-02-15
**Verdict:** PASS

---

## Implementation Summary

Added `AuditLogger._load_history()` (42 lines) called from `__init__` after `_open_log_file()`.

**Algorithm:**
1. Glob `log_dir` for `audit_*.jsonl` files sorted lexicographically (= chronologically).
2. Read all lines from each file in order; skip files with `OSError`.
3. Truncate to last `_max_memory_entries` raw lines before parsing (cheap cap).
4. Parse each line as JSON; skip malformed lines silently.
5. Set `self._entries = parsed_entries`.

**Files changed:**
- `src/mcpbridge_wrapper/webui/audit.py` — `_load_history()` + one call in `__init__`
- `tests/unit/webui/test_audit.py` — 4 new tests in `TestStartupHistoryLoad`

---

## Quality Gates

| Gate | Result |
|---|---|
| `pytest tests/unit/webui/test_audit.py` | **28/28 passed** |
| `pytest` (full suite) | **386 passed, 5 skipped** |
| Coverage (main modules) | **96.2%** (≥90% ✅; webui/* excluded per pyproject.toml) |
| `ruff check src/` | **All checks passed** |
| `mypy src/` | **No issues in 12 source files** |

---

## Acceptance Criteria

- [x] New `AuditLogger` over a dir with existing JSONL exposes those entries (`test_startup_loads_existing_jsonl`)
- [x] Entries loaded in chronological order (`test_startup_multiple_files_chronological_order`)
- [x] Malformed JSONL lines skipped without raising (`test_startup_skips_malformed_lines`)
- [x] Startup load capped at `_max_memory_entries` (`test_startup_respects_max_memory_entries`)
- [x] `test_initial_state` (empty tmpdir) still passes — 0 entries for empty dir
- [x] All 28 existing audit tests pass unchanged
- [x] Ruff clean, mypy clean

---

## Limitations / Out of Scope

- Live cross-process streaming: entries written by a sibling process *after* the web server starts are still not reflected in-memory. This fix provides **startup visibility only**. Full live cross-process sharing deferred to Phase 13 broker work.
