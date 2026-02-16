# Validation Report: FU-P12-T2-1

**Task:** Fix stacking click event listeners in `updateLatencyTable`
**Date:** 2026-02-16
**Verdict:** PASS

---

## Change Summary

Moved the delegated click handler for `.param-toggle-btn` out of
`updateLatencyTable` (which runs every ~2 s) into `setupEventHandlers` (which runs
once at init). The handler is now attached to `el("latency-table")` instead of
`tbody`, keeping the same event-delegation pattern.

**File changed:** `src/mcpbridge_wrapper/webui/static/dashboard.js`
- Removed `tbody.addEventListener("click", …)` block from `updateLatencyTable` (lines 332-350 prior to fix)
- Added equivalent `el("latency-table").addEventListener("click", …)` in `setupEventHandlers` (lines 570-588)

---

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest` | ✅ 465 passed, 5 skipped |
| `ruff check src/` | ✅ All checks passed |
| `pytest --cov` | ✅ 95.6% (≥ 90% required) |
| `mypy src/` | N/A — not configured |

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| `updateLatencyTable` contains no `addEventListener` call | ✅ |
| `setupEventHandlers` registers exactly one delegated click handler on `el("latency-table")` | ✅ |
| Toggle expand/collapse behaviour unchanged | ✅ (same handler logic) |
| `fetchParamPatterns` called exactly once per click regardless of prior refresh count | ✅ (single registered listener) |
| All existing tests pass | ✅ 465 passed |
