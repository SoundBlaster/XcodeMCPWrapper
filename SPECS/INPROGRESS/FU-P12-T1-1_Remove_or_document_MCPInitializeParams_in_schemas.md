# PRD: FU-P12-T1-1 — Remove or document `MCPInitializeParams` in schemas

**Created:** 2026-02-18
**Priority:** P3
**Branch:** `codex/feature/FU-P12-T1-1-remove-or-document-mcpinitializeparams`
**Status:** PLAN

---

## 1. Problem Statement

`MCPInitializeParams` exists in `src/mcpbridge_wrapper/schemas.py` but has no
usage in runtime code or tests. This creates unnecessary schema surface and can
mislead future maintainers into thinking there is a dedicated initialize-params
model contract in active use.

---

## 2. Scope

### In Scope
- Remove `MCPInitializeParams` if it is unused and not required for compatibility.
- Ensure existing request parsing (`MCPParams.clientInfo`) remains unchanged.
- Run full project quality gates and capture results.

### Out of Scope
- Any behavior changes to initialize request handling.
- Broader schema refactors unrelated to this unused model.

---

## 3. Deliverables

1. `src/mcpbridge_wrapper/schemas.py`
- Remove the unused `MCPInitializeParams` model and related dead comments.

2. Validation evidence
- Search evidence confirming no remaining references.
- Full quality gate results in validation report.

3. `SPECS/INPROGRESS/FU-P12-T1-1_Validation_Report.md`
- Record pass/fail outcomes for required checks.

---

## 4. Acceptance Criteria

- [ ] `MCPInitializeParams` is removed or has a clear, tested usage.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T1 ✅

---

## 6. Risks and Mitigations

- **Risk:** Hidden imports of `MCPInitializeParams` outside obvious call sites.
  - **Mitigation:** Run repository-wide search and full test/type/lint gates.

---

## 7. Validation Plan

1. Remove model definition from `schemas.py`.
2. Confirm no references remain with `rg "MCPInitializeParams"`.
3. Run required quality gates and record outcomes.

