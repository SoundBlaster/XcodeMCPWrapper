# PRD: FU-P12-T3-2 — Add `error_code` column to audit CSV export

**Created:** 2026-02-19
**Priority:** P3
**Branch:** `codex/feature/FU-P12-T3-2-error-code-csv-export`
**Status:** PLAN

---

## 1. Problem Statement

`AuditLogger.export_csv()` uses a fixed CSV header list that excludes `error_code`.
As a result, exported audit files silently drop a useful diagnostic field even
when entries contain structured error metadata.

---

## 2. Scope

### In Scope
- Add `error_code` to CSV export headers in `AuditLogger.export_csv()`.
- Ensure rows include `error_code` values when present.
- Ensure rows emit empty strings for `error_code` when absent.
- Add/adjust unit tests in `tests/unit/webui/test_audit.py`.

### Out of Scope
- Audit schema redesign.
- New export formats.
- Dashboard UI changes.

---

## 3. Deliverables

1. CSV export update
- `src/mcpbridge_wrapper/webui/audit.py`
- `error_code` present in exported CSV columns.

2. Test coverage
- `tests/unit/webui/test_audit.py`
- Assertions for both present and missing `error_code` cases.

3. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T3-2_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] CSV export includes `error_code` column.
- [ ] Entries without `error_code` render empty string in that column.
- [ ] Existing CSV tests still pass.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T3 ✅

---

## 6. Risks and Mitigations

- **Risk:** Column order changes may break fragile tests or downstream CSV
  consumers expecting a fixed order.
  - **Mitigation:** Keep existing order and append `error_code` at the end to
    minimize disruption.

---

## 7. Validation Plan

1. Update export column list to include `error_code`.
2. Add/adjust test fixtures and assertions for CSV header + row values.
3. Run required quality gates and document results in validation report.

---
**Archived:** 2026-02-19
**Verdict:** PASS
