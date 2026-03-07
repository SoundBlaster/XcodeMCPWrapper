# P8-T1: Release version 0.4.2 to PyPI and MCP Registry

**Status:** In Progress
**Date:** 2026-03-07
**Priority:** P0
**Dependencies:** P7-T5 (completed)

---

## Objective

Cut the `0.4.2` release to publish all unreleased Phase 5–7 work accumulated since the `v0.4.1` tag:
- Phase 5: broker robustness improvements (--broker flag, auto-recovery, -32001 error, web-UI mismatch warning)
- Phase 6: broker daemon status surface, terminal frontend (TUI)
- Phase 7: broker console startup, doctor diagnostics, port-conflict recovery, TUI local fallback, broker UX docs

---

## Current State

| Artifact | Current value |
|----------|---------------|
| `pyproject.toml` version | `0.4.1` |
| `server.json` version | `0.4.1` |
| README badge | `v0.4.1` |
| Latest PyPI release | `0.4.1` |
| Latest git tag | `v0.4.1` (points to earlier commit, not HEAD) |
| Unreleased commits since tag | ~80 commits across P5–P7 |

---

## Deliverables

1. **`pyproject.toml`** — version bumped to `0.4.2`
2. **`server.json`** — version bumped to `0.4.2` (both root `version` and `packages[0].version`)
3. **`README.md`** — version badge updated to `v0.4.2`
4. **Git tag `v0.4.2`** — created on `main` (after PR merge) and pushed to `origin`
5. **GitHub Actions `publish-mcp.yml`** — triggered by tag, publishes to PyPI + MCP Registry

---

## Implementation Steps

### 1. Bump versions (make bump-version)
```bash
make bump-version VERSION=0.4.2
```
Updates `pyproject.toml` and `server.json` atomically via `scripts/publish_helper.py`.

### 2. Update README badge (make badge-version)
```bash
make badge-version TAG=v0.4.2
```
Updates the `<!-- version-badge:start -->` … `<!-- version-badge:end -->` block in `README.md`.

### 3. Run quality gates
- `pytest` — all tests pass
- `ruff check src/` — no lint errors
- `mypy src/` — type check passes
- `pytest --cov` — coverage ≥ 90%

### 4. Commit, push branch, open PR, merge to main

### 5. Tag and push (after merge)
```bash
git tag v0.4.2
git push origin v0.4.2
```
This triggers `publish-mcp.yml` → publishes to PyPI and MCP Registry.

---

## Acceptance Criteria

- [ ] `pyproject.toml` version = `0.4.2`
- [ ] `server.json` root `version` = `0.4.2`
- [ ] `server.json` `packages[0].version` = `0.4.2`
- [ ] README badge reflects `v0.4.2`
- [ ] All quality gates pass (pytest, ruff, mypy, coverage ≥ 90%)
- [ ] Git tag `v0.4.2` exists on `origin/main`
- [ ] `https://pypi.org/project/mcpbridge-wrapper/0.4.2/` is accessible
- [ ] GitHub Actions `publish-mcp.yml` run for `v0.4.2` shows all steps green

---

## Risk Notes

- The `publish-mcp.yml` tag push must happen on `main` after the PR merges — do NOT push the tag from the feature branch.
- `make badge-version` reads the latest git tag; run it with explicit `TAG=v0.4.2` to avoid reading `v0.4.1`.
- PyPI publish uses `skip-existing: true` so a re-run is safe if it partially fails.
