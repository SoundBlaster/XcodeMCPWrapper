# PRD: FU-P12-T3-1 — Document unused `error_message` parameter in `MetricsCollector.record_response`

**Created:** 2026-02-19
**Priority:** P3
**Branch:** `codex/feature/FU-P12-T3-1-document-error-message-param`
**Status:** PLAN

---

## 1. Problem Statement

`MetricsCollector.record_response()` accepts `error_message` to mirror the
shared-store API shape, but the in-memory collector never persists that value.
The current docstring does not explicitly state this, which can mislead future
maintainers.

---

## 2. Scope

### In Scope
- Update the `error_message` docstring in `MetricsCollector.record_response()`
  to explicitly note compatibility-only behavior.

### Out of Scope
- Any functional logic changes to metrics collection.
- Changes to `SharedMetricsStore` persistence behavior.
- API signature changes.

---

## 3. Deliverables

1. Docstring clarification
- `src/mcpbridge_wrapper/webui/metrics.py`
- Add explicit note: `error_message` is accepted for interface symmetry but not
  persisted in the in-memory collector.

2. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T3-1_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] Docstring clearly notes `error_message` is accepted for API symmetry but
  not stored in-memory.
- [ ] No functional behavior changes.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T3 ✅

---

## 6. Risks and Mitigations

- **Risk:** Wording may be too vague and still imply optional persistence.
  - **Mitigation:** Use direct phrasing: accepted for compatibility, ignored for
    storage in this collector.

---

## 7. Validation Plan

1. Update the target docstring line in `metrics.py`.
2. Run quality gates to confirm no behavior regressions.
3. Record results in validation report.

---
**Archived:** 2026-02-19
**Verdict:** PASS
