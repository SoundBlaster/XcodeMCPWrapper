# PRD — FU-P14-T5-1: Add macOS CI execution for broker socket-path regression coverage

## 1. Context

`P14-T5` stabilized `TestSocketPermissions` locally by using a short socket path. The prior failure mode (`AF_UNIX path too long`) is macOS-specific enough that Linux-only CI cannot reliably detect regressions in this area.

## 2. Objective

Add explicit macOS CI coverage for the broker socket path/permission regression test while keeping the existing Linux CI matrix unchanged.

## 3. Deliverables

- Update `.github/workflows/ci.yml` with a macOS job that runs the broker socket regression test.
- Include an in-workflow documentation note explaining why this macOS lane exists (AF_UNIX path-length sensitivity).
- Preserve existing Ubuntu test matrix versions and behavior.

## 4. Dependencies

- `P14-T5` (completed)

## 5. Implementation Plan

1. Add a new job (e.g., `test-macos-socket-regression`) in CI workflow:
   - `runs-on: macos-latest`
   - install dev dependencies with `pip install -e ".[dev]"`
   - run targeted regression test:
     - `pytest -q tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
2. Add an inline comment in workflow clarifying the AF_UNIX path-length macOS rationale.
3. Ensure existing `test` job matrix remains on `ubuntu-latest` and unchanged.

## 6. Acceptance Criteria

- GitHub Actions runs the broker socket permission/path regression test on a macOS runner for PRs.
- The macOS job appears as a distinct PR check and fails the workflow if the test fails.
- Existing Linux test matrix behavior remains unchanged.

## 7. Validation

Required FLOW quality gates:

- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov` (coverage >= 90%)

Additional targeted verification:

- `pytest -q tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Validate CI YAML syntax and that macOS job is included under `on.pull_request` triggers.

## 8. Out of Scope

- Expanding full multi-version test matrix to macOS.
- Changing runtime broker behavior.
