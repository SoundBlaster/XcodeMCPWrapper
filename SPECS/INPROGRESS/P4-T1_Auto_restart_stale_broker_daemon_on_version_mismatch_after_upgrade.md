# P4-T1 PRD — Auto-restart stale broker daemon on version mismatch after upgrade

## Task Metadata

- **Task ID:** P4-T1
- **Phase:** Phase 4: Broker Lifecycle Management
- **Priority:** P0
- **Dependencies:** none
- **Source:** `SPECS/Workplan.md` open task entry

## Objective Summary

Prevent stale broker daemons from surviving wrapper upgrades and silently serving old behavior to new `--broker` clients. The wrapper must use a single version source of truth, persist daemon runtime version in broker state, detect mismatch before proxy reuse, and automatically restart stale daemons. The CLI must also expose explicit lifecycle control (`--broker-status`, `--broker-stop`) so users and scripts can inspect and remediate broker state without manual PID/socket file handling.

The implementation scope includes runtime behavior, CLI surface, install/uninstall operational safety, docs, and regression tests. Backwards compatibility requirement: legacy daemons without a version file must still be accepted as compatible unless a mismatch can be proven.

## Success Criteria

1. `__version__` is derived from package metadata (`importlib.metadata`) instead of hard-coded constants.
2. Broker daemon writes `broker.version` on startup and removes it during shutdown/cleanup paths.
3. Proxy detects mismatched daemon version and auto-restarts stale daemon before connecting.
4. Missing `broker.version` file is treated as compatible (no forced restart).
5. `--broker-status` reports PID/status/version info and mismatch warning.
6. `--broker-stop` gracefully stops daemon, waits for exit, and removes pid/socket/version state files.
7. Install and uninstall scripts stop any running broker daemon before replacing/removing wrapper files.
8. Broker-mode docs describe new lifecycle commands and version management flow.
9. Required quality gates pass: `pytest`, `ruff check src/`, `mypy src/mcpbridge_wrapper`, `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` (>= 90%).

## Acceptance Tests

- Unit tests for `BrokerConfig.version_file` path derivation.
- Unit tests for daemon version-file write/remove and status payload version field.
- Unit tests for proxy version mismatch detection and restart behavior.
- Unit tests for `_parse_broker_args` handling of `--broker-status` and `--broker-stop`.
- CLI behavior validation:
  - `python -m mcpbridge_wrapper --broker-status`
  - `python -m mcpbridge_wrapper --broker-stop`
- Script-level behavior validation for install/uninstall broker-stop logic (covered by shell-path checks and existing script tests if present).

## Test-First Plan

1. Add/extend tests for version file state in broker config and daemon lifecycle.
2. Add/extend proxy tests for mismatch detection, backward-compatible no-version behavior, and stale daemon restart.
3. Add/extend main/CLI tests for new broker control flags and argument parsing.
4. Implement runtime logic minimally to satisfy new failing tests.
5. Update docs and scripts after runtime tests pass.
6. Run full quality gates and capture outputs in validation report.

## Implementation Plan (Hierarchical TODO)

### Phase A — Version Source and Broker State

- **Inputs:** Existing `__version__` declaration, `BrokerConfig`, daemon lifecycle logic.
- **Outputs:** Metadata-derived version string; `version_file` property; daemon writes/cleans version file; status includes version.
- **Verification:** New daemon/config unit tests pass and stale-lock cleanup removes version artifacts.

### Phase B — Proxy and CLI Lifecycle Controls

- **Inputs:** Proxy spawn/reuse flow, broker arg parsing and command dispatch in `__main__.py`.
- **Outputs:** Version mismatch detection + stale daemon restart; `--broker-status`; `--broker-stop` cleanup behavior.
- **Verification:** New proxy/main tests pass and manual status/stop commands return expected output/exit semantics.

### Phase C — Operational Scripts, Docs, and Validation

- **Inputs:** `scripts/install.sh`, `scripts/uninstall.sh`, `docs/broker-mode.md`, quality gate tooling.
- **Outputs:** Install/uninstall stop running daemon before file replacement/removal; docs updated for status/stop/version behavior; validation report.
- **Verification:** Required quality gates pass; acceptance criteria checklist fully satisfied.

## Decision Points and Constraints

- Use defensive behavior when metadata/version files are unavailable: prefer safe fallback over hard failure.
- Keep broker-stop idempotent (safe when daemon already dead or files are stale/corrupt).
- Avoid introducing behavior that depends on non-portable process APIs beyond existing macOS/Linux constraints.
- Keep implementation scoped to P4-T1 artifacts; do not refactor unrelated broker subsystems.

## Notes (Post-Completion Docs/Artifacts)

- Create `SPECS/INPROGRESS/P4-T1_Validation_Report.md` with command evidence and verdict.
- Archive PRD and validation report to `SPECS/ARCHIVE/P4-T1_Auto_restart_stale_broker_daemon_on_version_mismatch_after_upgrade/`.
- Mark `P4-T1` complete in `SPECS/Workplan.md` and update `SPECS/ARCHIVE/INDEX.md`.
- Create and archive `REVIEW_p4_t1_broker_version_restart.md` after review.
