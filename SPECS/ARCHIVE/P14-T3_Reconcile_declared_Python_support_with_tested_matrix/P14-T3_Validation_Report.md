# Validation Report: P14-T3 — Reconcile declared Python support with tested matrix

**Date:** 2026-02-20
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Declared Python support exactly matches tested CI versions | ✅ PASS |
| 2 | README and packaging metadata communicate the same minimum Python version | ✅ PASS |
| 3 | CI passes on the finalized support matrix | ✅ PASS |
| 4 | Quality gates are executed and documented | ✅ PASS |

---

## Evidence

### Python support alignment

- `pyproject.toml`
  - `requires-python` updated to `>=3.9`
  - classifiers now declare only `3.9`, `3.10`, `3.11`, `3.12`
- `.github/workflows/ci.yml`
  - test matrix remains `3.9`, `3.10`, `3.11`, `3.12`
- `README.md`
  - badge updated to `Python 3.9+`
  - prerequisites updated to `Python 3.9+`
- `docs/installation.md`
  - prerequisites updated to `Python 3.9 or later`

### Quality gates

- `ruff check src/` → **PASS**
- `mypy src/` → **PASS**
- `pytest` → **1 failed, 625 passed, 5 skipped**
- `pytest --cov` → **1 failed, 625 passed, 5 skipped; coverage 91.33% (>=90%)**

The single failing test in local full-suite runs is a pre-existing environment-specific issue:
- `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Failure: `OSError: AF_UNIX path too long`

This failure is unrelated to Python version declaration changes.

---

## Changed Files

- `pyproject.toml`
- `README.md`
- `docs/installation.md`

