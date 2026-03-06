# P1-T11 — Update Test Coverage Badge in README with Actual Numbers

**Task ID:** P1-T11
**Priority:** P2
**Phase:** Phase 1 — Documentation
**Status:** In Progress

## Objective

Bring the README coverage display back in sync with the current codebase. The repository currently publishes a coverage badge and a duplicate coverage metric in the Performance section, both with a hard-coded value. This task uses the current `pytest --cov` result as the source of truth and updates the README so users see the real measured percentage instead of a stale number.

## Success Criteria

- The README coverage badge value matches the validated coverage percentage from the task run.
- The README Performance section uses the same coverage value as the badge.
- No other README badges, links, or formatting regress.

## Test-First Plan

1. Run `pytest --cov` before editing to capture the current total coverage percentage.
2. Inspect the existing README badge block and the Performance section so only the intended numeric values change.
3. After the README update, rerun the required quality gates and confirm the measured coverage still matches the updated documentation.

## Execution Plan

### Phase 1: Capture the coverage baseline

- Run the repository quality gates, especially `pytest --cov`, and record the reported total coverage percentage.
- Treat the reported total as the only number allowed in the README for this task.

### Phase 2: Update README coverage references

- Update the Shields.io coverage badge in `README.md` to the validated percentage.
- Update the Performance section coverage bullet to the same percentage.
- Keep the badge link target and surrounding badge layout unchanged unless inspection shows a formatting issue.

### Phase 3: Validate and document

- Re-run the required FLOW quality gates: `pytest`, `ruff check src/`, `mypy src/`, and `pytest --cov`.
- Create `SPECS/INPROGRESS/P1-T11_Validation_Report.md` with command results, the final coverage percentage, and acceptance-criteria checks.

## Decision Points and Constraints

- The coverage percentage must come from the local validation run performed during EXECUTE, not from archived docs or prior reports.
- This task is documentation-only; do not introduce new badge automation unless the existing files make it necessary to complete the update safely.
- If coverage output differs between repeated runs, use the final post-change validation run as the canonical value recorded in the validation report and README.

## Out of Scope

- Adding a new Make target or script for coverage badge maintenance.
- Changing non-coverage README content.
- Modifying test code solely to raise coverage.

## Notes

- Recheck the first 20 lines of `README.md` after editing so the badge row remains readable.
- Recheck the Performance section so there is no mismatch between the badge and the textual metric.

---
**Archived:** 2026-03-06
**Verdict:** PASS
