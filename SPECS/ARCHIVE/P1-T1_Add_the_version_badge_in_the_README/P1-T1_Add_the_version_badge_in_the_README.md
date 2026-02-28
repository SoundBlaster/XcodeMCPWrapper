# P1-T1 — Add the version badge in the README.md

**Task ID:** P1-T1  
**Phase:** Phase 1: Documentation  
**Priority:** P2  
**Dependencies:** none  
**Status:** Planned

## Objective

Implement maintainable automation for the README version badge so it can be updated from git tags with a small, test-covered script and ergonomic `make` commands.

## Success Criteria

- `README.md` contains a version badge wrapped in stable start/end markers.
- `scripts/update_version_badge.py` updates only the marker block using either `--tag` or latest tag.
- Script behavior is covered by unit tests for success and failure paths.
- `Makefile` exposes update and check commands for local/CI usage.
- Quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with coverage >= 90%.

## Test-First Plan

1. Add tests for tag normalization, badge block rendering, marker replacement, and check/update flows.
2. Refactor script internals to reduce function complexity and keep logic focused/testable.
3. Run targeted script tests, then full project quality gates.

## Execution Plan

### Phase A: Script Refactor
- **Inputs:** current `scripts/update_version_badge.py`, README marker contract
- **Outputs:** smaller helper functions, clearer error paths, idempotent update behavior
- **Verification:** unit tests for pure helpers and CLI behavior

### Phase B: Test Coverage
- **Inputs:** script contract and expected README badge format
- **Outputs:** `tests/unit/test_update_version_badge.py`
- **Verification:** `pytest tests/unit/test_update_version_badge.py -v`

### Phase C: Integration and Tooling
- **Inputs:** updated script and `Makefile`
- **Outputs:** validated `badge-version` / `badge-version-check` commands
- **Verification:** dry-run and check command execution; full quality-gate run

## Notes

- Keep implementation dependency-free and Python 3.9-compatible.
- Preserve unrelated README badges and formatting.
- Do not rewrite the full README file when marker block is unchanged.

---
**Archived:** 2026-02-28
**Verdict:** PASS
