# BUG-T8: Audit Log Cross-Process Visibility

**Type:** Bug Fix
**Priority:** P0
**Branch:** feature/BUG-T8-audit-log-cross-process-visibility
**Created:** 2026-02-15

---

## Problem Statement

`AuditLogger` initialises with an empty `self._entries` list. In multi-process setups
(Cursor, Zed) the process that binds the web UI port often handles only the `initialize`
handshake; subsequent tool calls arrive in sibling wrapper processes whose `AuditLogger`
instances are never visible to the web server. The dashboard therefore shows only 1 entry
while "Per-Tool Latency Statistics" (backed by SQLite) shows the full history.

---

## Root Cause

`AuditLogger.__init__` opens its JSONL file in append mode (`"a"`) but never reads existing
entries back into `self._entries`. The `/api/audit` endpoint reads only from `self._entries`,
so it cannot see any data written by other processes.

---

## Deliverables

### 1. `AuditLogger._load_history()` private method
Load at most `_max_memory_entries` entries (most-recent-first) from all `audit_*.jsonl`
files in `log_dir` into `self._entries` at startup.

Algorithm:
1. Glob `log_dir` for `audit_*.jsonl` files, sorted by filename ascending (filenames are
   `audit_YYYYMMDD_HHMMSS.jsonl` so lexicographic order = chronological order).
2. Read all lines from all files; collect as a flat list.
3. Truncate to the last `_max_memory_entries` lines (most recent).
4. Parse each line as JSON; skip malformed lines silently.
5. Set `self._entries = parsed_entries`.

### 2. Call `_load_history()` from `__init__`
Add one call at the end of `__init__`, after `_open_log_file()`.

### 3. Tests in `tests/unit/webui/test_audit.py`

| Test | Description |
|---|---|
| `test_startup_loads_existing_jsonl` | Write entries with logger A, close, create logger B in same dir → B sees A's entries |
| `test_startup_respects_max_memory_entries` | Pre-write > 10000 lines; B loads exactly 10000 |
| `test_startup_skips_malformed_lines` | JSONL file contains non-JSON line; B loads valid entries only |
| `test_startup_multiple_files` | Two rotated JSONL files; B sees entries from both, in chronological order |
| `test_startup_empty_dir_still_zero` | tmpdir has no JSONL; entry count is 0 (existing `test_initial_state` already covers) |

---

## Acceptance Criteria

- [ ] `AuditLogger` initialised over a directory with existing JSONL files exposes those entries via `get_entries()` and `get_entry_count()`
- [ ] Entries are loaded in chronological order (oldest first in `_entries`, newest first in `get_entries()` due to `reversed`)
- [ ] Malformed JSONL lines are skipped without raising
- [ ] Startup load is capped at `_max_memory_entries` (10 000), taking the most-recent N
- [ ] `test_initial_state` (empty tmpdir) still passes — load returns 0 entries for empty dir
- [ ] All existing tests pass unchanged
- [ ] `pytest --cov` coverage ≥ 90%
- [ ] `ruff check src/` clean
- [ ] `mypy src/` clean

---

## Out of Scope

- SQLite-backed shared audit store (Option B from BUG-T8 workplan entry) — deferred until Phase 13 broker work clarifies architecture
- Live cross-process streaming (writes from sibling process after startup are still not reflected; this fix gives startup visibility only)

---

## Dependencies

- `P10-T1` ✅ — `AuditLogger` foundation
- `BUG-T6` ✅ — port-collision fix that surfaces this bug

---

## File Change Summary

| File | Change |
|---|---|
| `src/mcpbridge_wrapper/webui/audit.py` | Add `_load_history()`, call from `__init__` |
| `tests/unit/webui/test_audit.py` | Add 4 new test cases for startup loading |
