# Validation Report — P9-T4: Create the publishing helper

**Date:** 2026-02-13  
**Verdict:** PASS

## Scope

Implemented a new publishing helper to perform coordinated version updates for release publishing, documented usage in publishing docs, and added tests.

## Deliverables

- `scripts/publish_helper.py` created
- `tests/unit/test_publish_helper.py` created
- `PUBLISHING.md` updated with helper usage and Makefile examples
- `Makefile` updated with `bump-version` target

## Acceptance Criteria Check

- [x] Running helper updates `pyproject.toml` and `server.json` to same version
- [x] Invalid semantic versions are rejected with clear error
- [x] `--dry-run` prints planned changes and does not modify files
- [x] Helper prints release commands (`git add`, `commit`, `tag`, `push`)
- [x] Existing tests and quality gates pass

## Commands Executed

- `pytest tests/unit/test_publish_helper.py -v`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`
- `python scripts/publish_helper.py 0.3.3 --dry-run`

## Results

- `pytest`: PASS (`345 passed, 5 skipped`)
- `ruff check src/`: PASS
- `mypy src/`: PASS
- `pytest --cov`: PASS (`Total coverage: 96.62%`, threshold 90%)
- Manual dry-run of helper: PASS (correct planned updates and guidance output)

## Notes

Test warnings seen during full suite were pre-existing environment/runtime warnings (websocket deprecations and transient port 8080 binding from threaded Web UI test), not regressions from this task.
