# PRD: FU-P12-T1-2 — Add code comment clarifying stdin-only client capture in `on_request`

**Created:** 2026-02-18
**Priority:** P3
**Branch:** `codex/feature/FU-P12-T1-2-stdin-only-capture-comment`
**Status:** PLAN

---

## 1. Problem Statement

`on_request()` in `src/mcpbridge_wrapper/__main__.py` captures client metadata
from `initialize` requests that arrive from stdin. This is intentional, but the
scope is not obvious without reading stream-direction assumptions.

---

## 2. Scope

### In Scope
- Add a concise code comment near initialize client-capture logic.
- Clarify that capture is intentionally stdin-only (client -> wrapper path).
- Keep behavior and data flow unchanged.

### Out of Scope
- Any functional changes to request/response handling.
- Additional telemetry or dashboard behavior changes.

---

## 3. Deliverables

1. `src/mcpbridge_wrapper/__main__.py`
- Add a comment by the client info capture block in `on_request()`.

2. Validation evidence
- Confirm no runtime behavior changes.
- Run required quality gates and document results.

3. `SPECS/INPROGRESS/FU-P12-T1-2_Validation_Report.md`
- Record command outcomes and verdict.

---

## 4. Acceptance Criteria

- [ ] Comment clearly states stdin-only capture direction.
- [ ] No functional changes are introduced.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T1 ✅

---

## 6. Risks and Mitigations

- **Risk:** Comment wording may be ambiguous and still invite misinterpretation.
  - **Mitigation:** Use explicit direction language (`stdin`, `client -> wrapper`) and keep it adjacent to the relevant block.

---

## 7. Validation Plan

1. Insert the clarifying comment in `on_request()`.
2. Run full quality gates.
3. Capture results and verdict in validation report.

---
