# Validation Report — P1-T1: Add the version badge in the README.md

**Date:** 2026-02-28  
**Verdict:** PASS

## Scope

Implemented README version badge automation with `make` helpers, refactored the badge update script into a plan/apply flow, and added dedicated unit tests for the new script behavior.

## Deliverables

- `README.md` updated with marker-wrapped version badge block
- `Makefile` updated with `badge-version` and `badge-version-check` targets
- `scripts/update_version_badge.py` created and refactored for testability
- `tests/unit/test_update_version_badge.py` created with explicit script behavior coverage

## Acceptance Criteria Check

- [x] `README.md` includes a visible version badge near the heading/badges area
- [x] Badge links to canonical GitHub release tag page
- [x] Script updates/checks badge from explicit or latest tag
- [x] Script has dedicated unit tests for core and CLI behavior

## Commands Executed

- `pytest tests/unit/test_update_version_badge.py -v`
- `python3 -m ruff check --fix scripts/update_version_badge.py tests/unit/test_update_version_badge.py`
- `python3 -m ruff check scripts/update_version_badge.py tests/unit/test_update_version_badge.py`
- `PYTHONPATH=src pytest`
- `python3 -m ruff check src/`
- `mypy src/`
- `PYTHONPATH=src pytest --cov`
- `make badge-version-check`

## Results

- Targeted script tests: PASS (`18 passed`)
- Script/test linting: PASS
- `pytest`: PASS (`715 passed, 5 skipped`)
- `ruff check src/`: PASS
- `mypy src/`: PASS (`18 source files checked`)
- `pytest --cov`: PASS (`Total coverage: 91.72%`, threshold 90%)
- `make badge-version-check`: PASS (`README version badge already up to date (v0.3.3)`)

## Notes

- Running plain `pytest` without `PYTHONPATH=src` failed in this environment due `ModuleNotFoundError: mcpbridge_wrapper` during collection. Re-running with `PYTHONPATH=src` resolved the environment issue and all tests passed.
