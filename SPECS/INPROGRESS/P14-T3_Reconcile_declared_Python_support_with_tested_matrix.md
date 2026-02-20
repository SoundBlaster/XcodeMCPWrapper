# PRD: P14-T3 — Reconcile declared Python support with tested matrix

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Dependencies:** none

---

## 1. Objective

Align declared Python compatibility in package metadata and user-facing docs with
what CI continuously tests, so support claims are explicit and verifiable.

---

## 2. Problem Summary

Current state is inconsistent:
- CI test matrix runs Python `3.9`, `3.10`, `3.11`, `3.12`.
- `pyproject.toml` declares `requires-python = ">=3.7"` and includes 3.7/3.8
  classifiers.
- `README.md` and `docs/installation.md` still state Python `3.7+`.
- Ruff target version is configured for `py37`.

This overstates supported versions relative to continuously tested versions.

---

## 3. Design

### 3.1 Canonical support floor

Set minimum supported Python to `3.9` to match the lowest version in CI.

### 3.2 Metadata alignment

Update `pyproject.toml`:
- `requires-python` to `>=3.9`
- remove 3.7/3.8 classifiers
- keep classifiers for 3.9–3.12
- set Ruff `target-version` to `py39`

### 3.3 Documentation alignment

Update user-facing docs to state Python `3.9+` consistently:
- README badge and prerequisite line
- Installation guide prerequisites

---

## 4. Files To Change

| File | Change |
|------|--------|
| `pyproject.toml` | Align minimum Python and classifiers with CI-tested matrix; update Ruff target version |
| `README.md` | Update Python badge and prerequisites to 3.9+ |
| `docs/installation.md` | Update prerequisite Python floor to 3.9+ |
| `SPECS/INPROGRESS/P14-T3_Validation_Report.md` | Record quality gates and acceptance evidence |

---

## 5. Acceptance Criteria

- [ ] Declared Python support exactly matches tested CI versions.
- [ ] README and packaging metadata communicate the same minimum Python version.
- [ ] CI passes on the finalized support matrix.
- [ ] Quality gates are executed and documented.

