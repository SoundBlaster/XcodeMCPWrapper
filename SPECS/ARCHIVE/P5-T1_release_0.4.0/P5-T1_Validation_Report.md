# P5-T1 Validation Report — Release 0.4.0 Preparation

**Task:** P5-T1 — Release 0.4.0 to PyPI and MCP Registry
**Date:** 2026-03-06
**Branch:** `codex/feature/P5-T1-release-0.4.0`
**Verdict:** PASS

---

## Quality Gate Results

### 1. `make test` (pytest + coverage)

```
785 passed, 5 skipped, 2 warnings in 8.73s
Coverage: 90.91% (required: 90.0%) — PASS
```

Coverage by module:

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| `__init__.py` | 8 | 0 | 100.0% |
| `__main__.py` | 455 | 26 | 93.0% |
| `bridge.py` | 87 | 2 | 96.6% |
| `broker/daemon.py` | 268 | 23 | 89.4% |
| `broker/proxy.py` | 230 | 33 | 85.7% |
| `broker/transport.py` | 359 | 31 | 87.8% |
| `broker/types.py` | 43 | 0 | 100.0% |
| `schemas.py` | 58 | 3 | 94.3% |
| `transform.py` | 92 | 2 | 95.8% |
| **TOTAL** | **1609** | **120** | **90.91%** |

### 2. `make lint` (ruff check)

```
All checks passed!
```

### 3. `make format-check` (ruff format)

```
49 files already formatted
```

### 4. `make typecheck` (mypy)

```
Success: no issues found in 18 source files
```

### 5. `make doccheck-all` (DocC sync)

```
✓ DocC sync checks passed across unstaged, staged, and branch scopes
```

### 6. `make package-assets-check` (Web UI assets in wheel + sdist)

```
Checked wheel: mcpbridge_wrapper-0.4.0-py3-none-any.whl
Checked sdist: mcpbridge_wrapper-0.4.0.tar.gz
OK: Required Web UI static assets are present in wheel and sdist.
```

---

## Release Artifact Verification

| Artifact | Value | Status |
|----------|-------|--------|
| `pyproject.toml` version | `0.4.0` | PASS |
| `server.json` version | `0.4.0` | PASS |
| `server.json packages[0].version` | `0.4.0` | PASS |
| `CHANGELOG.md [0.4.0]` date | `2026-03-06` (updated from `2026-02-20`) | PASS |
| CI/CD workflow (`publish-mcp.yml`) trigger | `push: tags: ["v*"]` | PASS |
| PyPI publish method | OIDC via `pypa/gh-action-pypi-publish@release/v1` | PASS |
| MCP Registry publish method | `mcp-publisher publish` via `github-oidc` | PASS |

---

## CHANGELOG Change

- **Before:** `## [0.4.0] - 2026-02-20`
- **After:** `## [0.4.0] - 2026-03-06`

---

## Summary

All six quality gates pass. The package builds correctly with Web UI assets included in both wheel and sdist. The CHANGELOG date has been updated to match the actual release date. Version metadata is consistent across `pyproject.toml`, `server.json`, and the `CHANGELOG.md` header. The CI/CD publish pipeline is tag-triggered and requires no additional configuration before the human operator creates the `v0.4.0` tag.
