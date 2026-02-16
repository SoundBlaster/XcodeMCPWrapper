## REVIEW REPORT — FU-P12-T2-1: Fix stacking click listeners in updateLatencyTable

**Scope:** origin/main..HEAD
**Files:** 1 (dashboard.js)
**Date:** 2026-02-16

---

### Summary Verdict

- [x] Approve

---

### Critical Issues

None.

---

### Secondary Issues

None.

---

### Architectural Notes

- The fix correctly moves the delegated click handler from `updateLatencyTable`
  (called every ~2 s by the polling loop) into `setupEventHandlers` (called once at
  `init()`), eliminating listener stacking entirely.
- Attaching to `el("latency-table")` (the stable `<table>` element) rather than
  `tbody` (whose children are rebuilt on each poll) is the right approach: the table
  element is present in the static HTML and survives all DOM rebuilds.
- Event delegation via `e.target.closest(".param-toggle-btn")` is preserved
  unchanged, so the handler correctly targets dynamically created buttons regardless
  of when they were inserted.
- The change is a pure refactor (no logic changes); the handler body is identical to
  the original.

---

### Tests

- 465 tests pass; 5 skipped. Coverage 95.6% (requirement: ≥90%).
- No JS unit tests exist for dashboard.js — this is consistent with the existing
  test suite which covers only the Python backend. No gap introduced.

---

### Next Steps

- No actionable issues found. FOLLOW-UP skipped.
