# P8-T1: Support Apple DocC for Documentation Publishing

**Task ID:** P8-T1  
**Status:** PLANNED  
**Priority:** P2  
**Phase:** 8 - Documentation Publishing  
**Date:** 2026-02-08

---

## 1. Overview

### 1.1 Goal
Set up Apple DocC documentation generation and automated publishing to GitHub Pages at `soundblaster.github.io/mcpbridge-wrapper`.

### 1.2 Context
This is a Python project, but DocC can still be used for documentation through Swift Package Manager's documentation generation capabilities. The existing docs will be converted/integrated into DocC format.

### 1.3 Constraints
- Must use GitHub Pages for hosting
- Must auto-deploy on pushes to main
- Must work with existing soundblaster.github.io setup

---

## 2. Deliverables

| # | Deliverable | Location | Purpose |
|---|-------------|----------|---------|
| 1 | GitHub Actions workflow | `.github/workflows/docs.yml` | Automated DocC build and deploy |
| 2 | DocC documentation catalog | `mcpbridge-wrapper.docc/` | DocC documentation source |
| 3 | GitHub Pages config | `.github/workflows/docs.yml` | Pages deployment settings |

---

## 3. Implementation Plan

### 3.1 Create GitHub Actions Workflow

Create `.github/workflows/docs.yml` with:
- Trigger on push to main and PRs
- macOS-14 runner with Xcode latest-stable
- DocC build with static hosting transformation
- Deploy to GitHub Pages only on main branch pushes

### 3.2 Create DocC Documentation Catalog

Create `mcpbridge-wrapper.docc/` containing:
- `mcpbridge-wrapper.md` - Main documentation page
- `GettingStarted.md` - Installation and quick start
- `Configuration.md` - Configuration for Cursor, Claude, Codex
- `Troubleshooting.md` - Common issues and solutions
- `Articles/` folder for additional documentation

### 3.3 Configure GitHub Pages

Ensure repository settings enable GitHub Pages from GitHub Actions.

---

## 4. Acceptance Criteria

- [ ] AC1: GitHub Actions workflow exists at `.github/workflows/docs.yml`
- [ ] AC2: Workflow triggers on push to main and PRs to main
- [ ] AC3: DocC builds successfully on macOS-14 with Xcode
- [ ] AC4: Documentation is deployed to `soundblaster.github.io/mcpbridge-wrapper`
- [ ] AC5: Deployment only happens on pushes to main (not PRs)
- [ ] AC6: Documentation includes all existing docs content

---

## 5. Dependencies

- P7-T10: Final README (completed)
- GitHub Pages enabled on repository
- soundblaster.github.io domain configured

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| DocC may not work well with Python projects | Medium | Use DocC for markdown documentation only, not API docs |
| GitHub Pages path conflicts | Low | Use `mcpbridge-wrapper` as hosting-base-path |
| Workflow permission issues | Low | Ensure proper permissions in workflow |

---

## 7. References

- GitHub Actions workflow template from Workplan.md
- Existing docs in `docs/` folder
- DocC documentation: https://www.swift.org/documentation/docc/
