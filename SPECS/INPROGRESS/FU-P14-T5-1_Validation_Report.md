# Validation Report — FU-P14-T5-1

**Task:** FU-P14-T5-1 — Add macOS CI execution for broker socket-path regression coverage  
**Date:** 2026-02-20  
**Verdict:** PASS

## Scope

- Add explicit macOS CI execution for socket path/permission regression coverage.
- Preserve existing Linux CI matrix behavior.

## Implemented Changes

- Updated `.github/workflows/ci.yml`:
  - Added `test-macos-socket-regression` job (`runs-on: macos-latest`).
  - Job installs dev dependencies and runs:
    - `pytest -q tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
  - Added inline workflow comment documenting AF_UNIX path-length sensitivity rationale.
- Existing Ubuntu test matrix job remains unchanged (`3.9`, `3.10`, `3.11`, `3.12`).

## Validation Commands

1. `pytest -q tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Result: PASS

2. `pytest`
- Result: PASS (`626 passed, 5 skipped`)

3. `ruff check src/`
- Result: PASS (`All checks passed!`)

4. `mypy src/`
- Result: PASS (`Success: no issues found in 18 source files`)

5. `pytest --cov`
- Result: PASS (`626 passed, 5 skipped`)
- Coverage: `91.33%` (threshold: `>= 90%`)

## Acceptance Criteria Check

- [x] GitHub Actions workflow includes a macOS runner job for broker socket permission/path regression test.
- [x] macOS check is a distinct CI job and will fail workflow if test fails.
- [x] Existing Linux matrix remains unchanged.

## Notes

- macOS workflow execution is validated by CI in the PR phase.
- Existing `websockets` deprecation warnings are unrelated to this task.
