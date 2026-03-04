# P1-T6 PRD — Update webui-setup.md and DocC mirror to use --broker in multi-agent examples

## Task Metadata

- **Task ID:** P1-T6
- **Phase:** Phase 1: Documentation
- **Priority:** P3
- **Dependencies:** P1-T4
- **Source:** `SPECS/Workplan.md` open task entry

## Objective Summary

Align remaining Web UI multi-agent setup documentation with the current broker CLI contract by replacing legacy `--broker-spawn` usage with `--broker`. The two target docs (`docs/webui-setup.md` and `Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md`) should match each other and reflect the same recommended command examples already adopted elsewhere in project docs.

This task is documentation-only and should not change runtime behavior. The goal is consistency, lower user confusion, and removal of stale examples that imply deprecated or removed flags are still preferred. The update should preserve surrounding guidance (single host broker, shared telemetry, web UI hosting constraints) while changing only the broker invocation form and any adjacent wording that explicitly references spawning.

## Success Criteria

1. Every multi-agent broker setup example in `docs/webui-setup.md` uses `--broker` (not `--broker-spawn`).
2. The mirrored sections in `Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md` match the updated canonical docs wording and commands.
3. `make doccheck-all` passes with no drift between docs and DocC mirrors.
4. Repository quality gates remain green (`pytest`, `ruff check src/`, `mypy src/mcpbridge_wrapper`, coverage >= 90%).

## Acceptance Tests

- Search assertions:
  - `rg --fixed-strings --line-number "--broker-spawn" docs/webui-setup.md Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md` returns no task-related example hits.
  - `rg --line-number "--broker" docs/webui-setup.md Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md` shows updated example commands.
- Validation command:
  - `make doccheck-all` exits successfully.
- Regression gates:
  - `pytest`
  - `ruff check src/`
  - `mypy src/mcpbridge_wrapper`
  - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## Test-First Plan

1. Inspect current docs and capture baseline grep output for `--broker-spawn` occurrences in both target files.
2. Define expected post-change command strings for each multi-agent section before editing.
3. Apply minimal textual edits to canonical docs first, then mirror the same edits to DocC.
4. Re-run targeted grep checks immediately after edits to verify stale flags are removed.
5. Run `make doccheck-all` before full quality gates to catch documentation drift early.
6. Run full required quality gates and record outcomes in validation report.

## Implementation Plan (Hierarchical TODO)

### Phase A — Baseline Audit

- **Inputs:** Current versions of `docs/webui-setup.md`, `Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md`.
- **Outputs:** List of exact sections/commands still using `--broker-spawn`.
- **Verification:** Grep results identify all target lines and no unrelated files are modified.

### Phase B — Documentation Updates

- **Inputs:** Baseline audit findings + current broker guidance from existing docs.
- **Outputs:** Updated broker examples and wording in both files.
- **Verification:** Side-by-side diff confirms command changes are intentional and mirrored.

### Phase C — Consistency and Quality Validation

- **Inputs:** Updated docs and repository quality tooling.
- **Outputs:** Passing `doccheck-all` and required quality gate outputs.
- **Verification:** Command exit codes are zero; validation report records command evidence and verdict.

## Decision Points and Constraints

- Keep scope strictly to P1-T6 artifacts unless validation reveals required synchronization edits.
- Prefer exact mirror consistency between canonical docs and DocC content.
- Avoid changing unrelated examples or historical notes unless they directly reference the removed flag in the target sections.
- This repository declares Python 3.7+ compatibility; use existing command targets without introducing new tooling assumptions.

## Notes (Post-Completion Docs/Artifacts)

- Produce `SPECS/INPROGRESS/P1-T6_Validation_Report.md` with full gate results and final verdict.
- Archive this PRD and the validation report into `SPECS/ARCHIVE/P1-T6_Update_webui_setup_and_DocC_mirror_to_use_broker_in_multi_agent_examples/` during ARCHIVE.
- Update `SPECS/ARCHIVE/INDEX.md` and mark the workplan task as completed once validated.

---
**Archived:** 2026-03-04
**Verdict:** PASS
