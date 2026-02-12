# PRD: P9-T3 — Release version 0.3.0 (Web UI Feature Release)

## 1. Objective

Ship `v0.3.0` as the Web UI release by updating package metadata, documenting release highlights, and preparing publish artifacts for PyPI and MCP Registry workflows.

## 2. Dependencies

- `P10-T3` (completed): main branch recovered and stable after Web UI merge
- `FU-REBUILD-P10-T1-6` (completed): uninstall/docs consistency fixes included before release

## 3. Deliverables

1. Version bump from `0.2.0` to `0.3.0` in:
   - `pyproject.toml`
   - `server.json`
2. Changelog entry:
   - `CHANGELOG.md` includes a dated `0.3.0` section with Web UI highlights
   - bottom reference link for `[0.3.0]`
3. Release execution notes:
   - tag/publish checklist captured in validation report with current execution status
4. Flow artifacts:
   - `SPECS/INPROGRESS/P9-T3_Validation_Report.md`
   - `SPECS/INPROGRESS/REVIEW_release-0.3.0.md`

## 4. Acceptance Criteria

- `pyproject.toml` project version is `0.3.0`
- `server.json` top-level and package versions are `0.3.0`
- `CHANGELOG.md` includes `[0.3.0] - 2026-02-13` with Web UI release summary
- Local quality gates all pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` with coverage `>= 90%`
- Validation report records release command status:
  - tag command prepared
  - push/publish verification status recorded (or explicitly marked as pending if not executed in this run)

## 5. Implementation Plan

1. Update version metadata files.
2. Add `0.3.0` changelog section with:
   - Web UI dashboard availability
   - operational controls and auditing features
   - packaging/docs polish completed since `0.2.0`
3. Run all required quality gates and capture outputs.
4. Document release command readiness and any non-local actions in validation report.

## 6. Risks and Mitigations

- Risk: publish steps require remote side effects (`git push`, tags, CI workflows).
  - Mitigation: record exact commands and execution status in validation report; only run side-effecting commands after local checks pass.
- Risk: release note drift from implemented features.
  - Mitigation: source highlights from merged P10/FU archive artifacts and current repository state.
