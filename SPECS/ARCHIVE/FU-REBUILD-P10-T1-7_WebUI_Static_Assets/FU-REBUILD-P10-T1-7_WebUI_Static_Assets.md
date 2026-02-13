# FU-REBUILD-P10-T1-7: Include Web UI static assets in published package artifacts

**Priority:** P1  
**Dependencies:** P10-T1, P9-T3  
**Status:** IN PROGRESS

## Problem Statement

Web UI starts successfully with:

`uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper --web-ui --web-ui-port 8080`

but opening `http://localhost:8080` shows fallback HTML:

`XcodeMCPWrapper Dashboard` / `Static files not found.`

The release wheel (`mcpbridge_wrapper-0.3.0-py3-none-any.whl`) includes Python modules in `mcpbridge_wrapper/webui/` but omits static frontend files in `mcpbridge_wrapper/webui/static/`.

## Deliverables

1. Packaging config includes `webui/static/*.html`, `webui/static/*.css`, `webui/static/*.js` in build artifacts (wheel and sdist).
2. Regression test ensures dashboard route serves real static-based HTML, not fallback content.
3. Validation report with artifact verification + quality gate results.
4. Workplan/next/archive artifacts updated per FLOW.

## Implementation Plan

### Task 1: Fix package data inclusion
- Update setuptools package-data configuration in `pyproject.toml`.
- Add `MANIFEST.in` rules to include static assets in source distributions.

### Task 2: Add runtime regression coverage
- Strengthen Web UI server test to fail if fallback HTML is served.
- Ensure test checks for static references (`/static/dashboard.css`, `/static/dashboard.js`).

### Task 3: Validate artifacts and quality gates
- Build wheel and verify static files are present in archive entries.
- Run required quality gates:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` (>=90%)
- Create `SPECS/INPROGRESS/FU-REBUILD-P10-T1-7_Validation_Report.md`.

## Acceptance Criteria

- [ ] Built wheel contains:
  - `mcpbridge_wrapper/webui/static/index.html`
  - `mcpbridge_wrapper/webui/static/dashboard.css`
  - `mcpbridge_wrapper/webui/static/dashboard.js`
- [ ] Web UI dashboard serves real page content (no `Static files not found.` fallback).
- [ ] Automated tests fail if static assets are missing at runtime.
- [ ] Required quality gates pass, with coverage >=90%.

## Affected Files

- `pyproject.toml`
- `MANIFEST.in` (new)
- `tests/unit/webui/test_server.py`
- `SPECS/INPROGRESS/FU-REBUILD-P10-T1-7_Validation_Report.md` (new)

---
**Archived:** 2026-02-13
**Verdict:** PASS
