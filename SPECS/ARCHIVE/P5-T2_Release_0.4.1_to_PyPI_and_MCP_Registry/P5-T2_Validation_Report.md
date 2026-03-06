# Validation Report: P5-T2 — Release 0.4.1 to PyPI and MCP Registry

**Date:** 2026-03-06
**Verdict:** PASS

---

## Changes Made

| File | Change |
|------|--------|
| `pyproject.toml` | `version = "0.4.1"` |
| `server.json` | `"version": "0.4.1"` (top-level and `packages[0].version`) |
| `CHANGELOG.md` | `[0.4.1] - 2026-03-06` entry added under `### Fixed` |

## Quality Gates

| Gate | Result | Detail |
|------|--------|--------|
| `pytest` | ✅ PASS | 785 passed, 5 skipped |
| `ruff check src/` | ✅ PASS | All checks passed |
| `mypy src/` | ✅ PASS | No issues found in 18 source files |
| `pytest --cov` | ✅ PASS | 90.81% coverage (≥ 90% required) |

## Acceptance Criteria

- [x] `pyproject.toml` version is `0.4.1`
- [x] `server.json` top-level and packages version is `0.4.1`
- [x] `CHANGELOG.md` has `[0.4.1]` entry with date `2026-03-06` and BUG-T9 fix noted
- [x] All quality gates pass
- [ ] `git tag v0.4.1` pushed to remote (post-merge, human action)
- [ ] PyPI publish succeeds (CI/CD post-tag)
- [ ] MCP Registry updated (CI/CD post-tag)

## Notes

`0.4.1` is a patch release containing the BUG-T9 fix (commit `b607410` + `26ede0c` on `main`, merged after the `v0.4.0` tag). The fix ensures the broker daemon sends `notifications/initialized` to the upstream before the `tools/list` probe, completing the MCP handshake correctly.

The remaining three acceptance criteria (tag push, PyPI, MCP Registry) are post-merge human actions that trigger CI/CD automatically.
