# Validation Report: P14-T2 — Align release metadata and changelog for 0.4.0

**Date:** 2026-02-20
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `pyproject.toml`, `server.json`, and `CHANGELOG.md` all reference `0.4.0` consistently | ✅ PASS |
| 2 | Changelog includes accurate notes for broker and Web UI work shipped since `0.3.2` | ✅ PASS |
| 3 | Release metadata passes existing build/publish validation checks | ✅ PASS |
| 4 | Quality gates are executed and documented | ✅ PASS |

---

## Evidence

### Version alignment

`0.4.0` is now present in all release metadata targets:
- `pyproject.toml` → `version = "0.4.0"`
- `server.json` → top-level `version` and `packages[0].version` are `"0.4.0"`
- `CHANGELOG.md` → new `## [0.4.0] - 2026-02-20` section and release reference link

### Changelog coverage

The new `0.4.0` entry includes:
- broker architecture and transport reliability highlights
- Web UI observability and analytics enhancements
- key compatibility and correctness fixes delivered after `0.3.2`

### Build and publish validation

- `python -m build` → **PASS** (exit 0)
- `pytest tests/unit/test_publish_helper.py` → **PASS** (`17 passed`)

### Quality gates

- `ruff check src/` → **PASS** (exit 0)
- `mypy src/` → **PASS** (exit 0)
- `pytest` → **1 failed, 625 passed, 5 skipped**
- `pytest --cov` → **1 failed, 625 passed, 5 skipped; coverage 91.33% (>=90%)**

Known pre-existing local failure:
- `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Error: `OSError: AF_UNIX path too long`

This failure is environment-specific and unrelated to release metadata/changelog changes.

---

## Changed Files

- `pyproject.toml`
- `server.json`
- `CHANGELOG.md`
- `SPECS/INPROGRESS/P14-T2_Validation_Report.md`
