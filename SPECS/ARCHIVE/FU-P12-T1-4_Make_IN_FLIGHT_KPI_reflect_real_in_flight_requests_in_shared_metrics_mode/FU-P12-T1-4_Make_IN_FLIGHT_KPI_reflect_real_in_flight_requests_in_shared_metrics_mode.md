# PRD: FU-P12-T1-4 — Make `IN FLIGHT` KPI reflect real in-flight requests in shared-metrics mode

**Created:** 2026-02-19
**Priority:** P2
**Branch:** `codex/feature/FU-P12-T1-4-in-flight-shared-metrics`
**Status:** PLAN

---

## 1. Problem Statement

In shared SQLite metrics mode, `SharedMetricsStore.get_summary()` returns
`"in_flight": 0` unconditionally. This causes the Web UI KPI to be misleading
and prevents operators from seeing currently outstanding requests.

---

## 2. Scope

### In Scope
- Implement process-safe computation of `in_flight` for shared metrics mode.
- Ensure in-flight count increases on `record_request` and decreases after
  matching `record_response` updates complete.
- Add unit tests for shared-store in-flight behavior, including multiple
  concurrent outstanding requests.

### Out of Scope
- Dashboard UI redesign.
- Changes to in-memory `MetricsCollector` in-flight behavior.
- Manual desktop verification of Xcode prompt workflows.

---

## 3. Deliverables

1. Shared metrics in-flight support
- `src/mcpbridge_wrapper/webui/shared_metrics.py`
- Replace hardcoded `in_flight: 0` with derived process-safe value.

2. Test coverage
- `tests/unit/webui/test_shared_metrics.py`
- Add/adjust tests proving non-zero while outstanding and zero after response.

3. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T1-4_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] `IN FLIGHT` KPI is greater than zero while requests are in progress and returns to zero after responses.
- [ ] Works correctly with multiple concurrent clients/processes using the shared metrics database.
- [ ] No regressions in existing dashboard metrics endpoints.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T1 ✅

---

## 6. Risks and Mitigations

- **Risk:** Counting unresolved requests purely by `latency_ms IS NULL` may
  include stale rows from abnormal process termination.
  - **Mitigation:** Scope in-flight query to current summary window to avoid
    indefinite inflation from old stale records.

- **Risk:** Request ID reuse across processes could mismatch response updates.
  - **Mitigation:** Keep existing update strategy unchanged and validate only
    aggregate outstanding-count behavior at store level.

---

## 7. Validation Plan

1. Implement shared in-flight counting in `get_summary()`.
2. Add tests for outstanding requests before and after response updates.
3. Run required quality gates and record outcomes.

---
**Archived:** 2026-02-19
**Verdict:** PASS
