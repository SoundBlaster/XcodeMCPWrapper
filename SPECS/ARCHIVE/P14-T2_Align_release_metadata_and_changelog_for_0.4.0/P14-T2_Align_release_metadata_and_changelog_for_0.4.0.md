# PRD: P14-T2 — Align release metadata and changelog for 0.4.0

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Dependencies:** P14-T1, P14-T3, P14-T4

---

## 1. Objective

Prepare a publishable `0.4.0` release by making package/registry version fields
consistent and documenting delivered functionality since `0.3.2` in
`CHANGELOG.md`.

---

## 2. Problem Summary

Release metadata is currently out of date:
- `pyproject.toml` still declares `0.3.3`
- `server.json` still declares `0.3.3` (top-level and package entry)
- `CHANGELOG.md` has no `0.4.0` entry summarizing broker and Web UI work

This blocks clear, auditable release preparation.

---

## 3. Design

### 3.1 Version metadata alignment

Update version values to `0.4.0` in:
- `pyproject.toml` (`project.version`)
- `server.json` (`version` and `packages[0].version`)

### 3.2 Changelog entry for 0.4.0

Add a new `0.4.0` section at the top of `CHANGELOG.md` that includes:
- release date
- key broker architecture and reliability changes
- key Web UI/observability improvements
- fixes and compatibility improvements delivered after `0.3.2`
- release link reference for `[0.4.0]`

### 3.3 Validation

Run standard quality gates and build validations:
- `ruff check src/`
- `mypy src/`
- `pytest`
- `pytest --cov` (coverage >= 90%)
- `python -m build`

Record results in `SPECS/INPROGRESS/P14-T2_Validation_Report.md`.

---

## 4. Files To Change

| File | Change |
|------|--------|
| `pyproject.toml` | Update package version to `0.4.0` |
| `server.json` | Update top-level and package version fields to `0.4.0` |
| `CHANGELOG.md` | Add `0.4.0` release entry and reference link |
| `SPECS/INPROGRESS/P14-T2_Validation_Report.md` | Capture execution evidence and gate outcomes |

---

## 5. Acceptance Criteria

- [ ] `pyproject.toml`, `server.json`, and `CHANGELOG.md` all reference `0.4.0` consistently.
- [ ] Changelog includes accurate notes for broker and Web UI work shipped since `0.3.2`.
- [ ] Release metadata passes existing build/publish validation checks.
- [ ] Quality gates are executed and documented.

---
**Archived:** 2026-02-20
**Verdict:** PASS
