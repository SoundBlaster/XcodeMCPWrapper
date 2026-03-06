# PRD: P5-T2 — Release 0.4.1 to PyPI and MCP Registry

**Status:** In Progress
**Priority:** P0
**Phase:** Phase 5: Release
**Date:** 2026-03-06

---

## Background

`v0.4.0` was tagged and released on 2026-03-06. After the tag, `BUG-T9` was merged into `main`: the broker daemon was not sending `notifications/initialized` before the `tools/list` probe, causing the upstream MCP handshake to stall and all client requests to time out. This critical bugfix must be shipped as `0.4.1`.

## Scope

Publish `mcpbridge-wrapper 0.4.1` as a patch release containing the BUG-T9 fix. This involves:

1. Bumping version to `0.4.1` in `pyproject.toml` and `server.json` via `publish_helper.py`.
2. Adding a `[0.4.1]` entry to `CHANGELOG.md` documenting the BUG-T9 fix.
3. Running all quality gates to confirm the release commit is clean.
4. Committing and pushing changes on the feature branch.
5. Merging to `main` via PR, then pushing `git tag v0.4.1` to trigger CI/CD.

## Deliverables

| File | Change |
|------|--------|
| `pyproject.toml` | `version = "0.4.1"` |
| `server.json` | `"version": "0.4.1"` in top-level and `packages[0].version` |
| `CHANGELOG.md` | `[0.4.1]` entry under `Fixed` |

## Quality Gates

- `pytest` — all tests pass (≥ 785 passing)
- `ruff check src/` — no lint errors
- `mypy src/` — no type errors
- `pytest --cov` — coverage ≥ 90%

## Acceptance Criteria

- [ ] `pyproject.toml` version is `0.4.1`
- [ ] `server.json` top-level and packages version is `0.4.1`
- [ ] `CHANGELOG.md` has `[0.4.1]` entry with date `2026-03-06` and BUG-T9 fix noted
- [ ] All quality gates pass
- [ ] `git tag v0.4.1` pushed to remote (post-merge, human action)
- [ ] PyPI publish succeeds (CI/CD post-tag)
- [ ] MCP Registry updated (CI/CD post-tag)

---
**Archived:** 2026-03-06
**Verdict:** PASS
