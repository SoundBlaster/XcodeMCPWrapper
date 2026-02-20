# Validation Report: P14-T4 — Replace deprecated setuptools license metadata with SPDX format

**Date:** 2026-02-20
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Build output no longer emits setuptools license deprecation warnings | ✅ PASS |
| 2 | Package metadata remains valid for PyPI and MCP registry publication | ✅ PASS |
| 3 | Existing `make check` pipeline remains green | ✅ PASS* |
| 4 | Quality gates are executed and documented | ✅ PASS |

\* Local full test-suite runs continue to show one pre-existing environment-specific failure (`AF_UNIX path too long`) that is unrelated to this task's packaging metadata changes.

---

## Evidence

### Metadata migration

Updated `pyproject.toml`:
- `project.license` changed from `{text = "MIT"}` to SPDX string `"MIT"`
- Added `project.license-files = ["LICENSE"]`
- Removed deprecated classifier `License :: OSI Approved :: MIT License`

### Build verification

- `python -m build` → **PASS** (exit 0)
- Build log contains packaged license file entries and no `SetuptoolsDeprecationWarning` related to license metadata.

### Quality gates

- `ruff check src/` → **PASS** (exit 0)
- `mypy src/` → **PASS** (exit 0)
- `pytest` → **1 failed, 625 passed, 5 skipped**
- `pytest --cov` → **1 failed, 625 passed, 5 skipped; coverage 91.33% (>=90%)**

Known pre-existing local failure:
- `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Error: `OSError: AF_UNIX path too long`

---

## Changed Files

- `pyproject.toml`
- `SPECS/INPROGRESS/P14-T4_Validation_Report.md`
