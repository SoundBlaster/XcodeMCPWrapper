# PRD: P14-T4 — Replace deprecated setuptools license metadata with SPDX format

**Status:** INPROGRESS
**Priority:** P2
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Dependencies:** none

---

## 1. Objective

Eliminate setuptools license metadata deprecation warnings in build output by
migrating to modern SPDX-based configuration.

---

## 2. Problem Summary

`python -m build` currently emits deprecation warnings because:
- `project.license` is configured as a TOML table (`{text = "MIT"}`), which is deprecated.
- `License :: OSI Approved :: MIT License` classifier is deprecated in favor of
  SPDX license expressions.

---

## 3. Design

### 3.1 Migrate to SPDX license expression

Update `pyproject.toml`:
- Set `project.license = "MIT"`.
- Add `project.license-files = ["LICENSE"]`.
- Remove deprecated license classifier.

### 3.2 Validation

Re-run `python -m build` and verify deprecation warnings no longer appear.
Also run standard quality gates (`ruff`, `mypy`, `pytest`, `pytest --cov`).

---

## 4. Files To Change

| File | Change |
|------|--------|
| `pyproject.toml` | Replace deprecated license metadata with SPDX string and license-files entry |
| `SPECS/INPROGRESS/P14-T4_Validation_Report.md` | Capture build output evidence and quality gate results |

---

## 5. Acceptance Criteria

- [ ] Build output no longer emits setuptools license deprecation warnings.
- [ ] Package metadata remains valid for PyPI and MCP registry publication.
- [ ] Existing `make check` pipeline remains green.
- [ ] Quality gates are executed and documented.


---
**Archived:** 2026-02-20
**Verdict:** PASS
