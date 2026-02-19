# PRD: FU-P12-T1-6 — Uniform HTML escaping in `renderClientWidgets`

**Created:** 2026-02-19
**Priority:** P3
**Branch:** `codex/feature/FU-P12-T1-6-uniform-html-escaping-client-widgets`
**Status:** PLAN

---

## 1. Problem Statement

`renderClientWidgets` in the dashboard escapes `name` and `version`, but does
not consistently escape all interpolated values (`count`, `lastSeen`) before
injecting HTML. This asymmetric pattern is low risk today but increases review
and audit complexity.

---

## 2. Scope

### In Scope
- Update `renderClientWidgets` so all interpolated values are passed through
  `escapeHtml()`.
- Add or update frontend tests to verify escaping is applied uniformly.

### Out of Scope
- Dashboard visual redesign.
- Backend metrics payload changes.
- Changes to `formatRelativeAge` behavior.

---

## 3. Deliverables

1. Uniform escaping in client widget rendering
- `src/mcpbridge_wrapper/webui/static/dashboard.js`
- Ensure `count` and `lastSeen` paths use `escapeHtml()` consistently.

2. Test coverage
- `tests/unit/webui/static/test_dashboard.js`
- Add/update assertions for escaped rendering values.

3. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T1-6_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] All interpolated values in `renderClientWidgets` are escaped.
- [ ] No visual/behavioral regression in client widget rendering.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- FU-P12-T1-3 ✅

---

## 6. Risks and Mitigations

- **Risk:** Escaping numeric values may alter formatting unexpectedly.
  - **Mitigation:** Keep formatting conversion stable (`String(...)`) and verify
    rendered output via tests.

- **Risk:** Duplicate escaping for derived strings could change displayed text.
  - **Mitigation:** Escape at the final interpolation boundary and validate with
    existing widget rendering tests.

---

## 7. Validation Plan

1. Apply uniform escaping in `renderClientWidgets`.
2. Add/update tests for escaped output paths.
3. Run full quality gates and capture results.

---
**Archived:** 2026-02-19
**Verdict:** PASS
