# PRD — P14-T5: Stabilize broker Unix-socket permission test against path-length limits

## 1. Context

`pytest -q` can fail on macOS with:

- `OSError: AF_UNIX path too long`

The failure occurs in `TestSocketPermissions.test_socket_created_with_0600_permissions`, where the test binds a Unix socket under `tmp_path / "broker.sock"`. On systems where pytest's temporary directory path is long, the resulting AF_UNIX path exceeds platform limits.

## 2. Objective

Make the socket-permission test deterministic across environments while preserving the original behavior check (`0600` permissions).

## 3. Deliverables

- Update `tests/unit/test_broker_transport.py` so socket-permission testing uses a short, deterministic socket base path under `/tmp`.
- Keep existing permission assertion unchanged in meaning (`0o600`).
- Add cleanup handling for temporary directories used by the test fixture/helper.

## 4. Dependencies

- FU-P13-T12 (socket permission/security behavior already implemented)

## 5. Implementation Plan

1. Add a dedicated helper for short socket paths in tests (or update existing test helper) using `tempfile.mkdtemp(dir="/tmp", prefix="mcp...")`.
2. Route `TestSocketPermissions.test_socket_created_with_0600_permissions` through that helper.
3. Ensure helper uses `try/finally` cleanup to avoid residue in `/tmp`.
4. Keep socket permission assertion logic exactly as before.

## 6. Acceptance Criteria

- `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions` passes with default pytest temp paths.
- Full `pytest -q` passes without `--basetemp` workaround.
- Test still verifies mode equals `0o600`.

## 7. Validation

Required quality gates per FLOW:

- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov` (coverage >= 90%)

Plus explicit check:

- `pytest -q tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`

## 8. Out of Scope

- Runtime broker socket path behavior in production code.
- Changes to non-test socket configuration defaults.

---
**Archived:** 2026-02-20
**Verdict:** PASS
