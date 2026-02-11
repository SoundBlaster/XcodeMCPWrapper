# PRD — P10-T3 Recover Main Branch After Accidental Web UI Merge

## Objective Summary
The goal of P10-T3 is to restore `main` to a releasable state after an accidental merge of the Phase 10 Web UI branch introduced regressions. This task is a stabilization task, not a feature expansion task. The implementation must preserve intended Web UI functionality from P10 while removing behavioral regressions that currently break quality gates or runtime behavior.

The recovery process will be evidence-driven: first identify concrete failing tests/lint/type checks and any reproducible runtime failures, then implement the smallest corrective patch set that resolves those failures. If a fix can be applied as a forward-fix without losing intended behavior, that is preferred over broad rollback. The result must be a branch that can be merged into `main` without carrying known breakages.

## Success Criteria and Acceptance Tests
Success criteria:
- `pytest` passes for the full repository test suite.
- `ruff check src/` and `mypy src/` pass.
- Coverage remains >= 90% with `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`.
- Web UI code path remains operational (no regressions to key modules under `src/mcpbridge_wrapper/webui/`).
- A written validation report documents commands, results, and final verdict.

Acceptance tests:
1. Reproduce current breakage via failing command(s) before fixes.
2. Add/adjust tests first for identified regression behavior (Outside-In where feasible).
3. Apply minimal code changes to satisfy tests.
4. Re-run full quality gates and map results to acceptance criteria.

## Test-First Plan
1. Run baseline quality gates and capture failures (`pytest`, `ruff`, `mypy`, coverage).
2. For each regression, create or update a failing test that demonstrates the specific broken behavior.
3. Implement minimal code to make that test pass.
4. Re-run targeted tests first, then full suite.
5. Only refactor after all tests are green.

## Hierarchical TODO Plan
### Phase A — Baseline Failure Discovery
- **Inputs:** Current `P10-T3` branch state, quality gate commands.
- **Outputs:** Regression inventory with failing commands and affected files.
- **Verification:** At least one reproducible failing signal is documented before making fixes.

### Phase B — Regression Repair (TDD)
- **Inputs:** Failing test cases from Phase A.
- **Outputs:** Focused production code and/or test corrections that remove regressions while preserving intended P10 behavior.
- **Verification:** Previously failing regression tests pass; no new failures introduced in related test modules.

### Phase C — Full Validation and Evidence
- **Inputs:** Updated codebase after Phase B.
- **Outputs:** Passing quality gates and `SPECS/INPROGRESS/P10-T3_Validation_Report.md` with command transcript summary and verdict.
- **Verification:** All required commands pass; acceptance criteria checklist marked PASS.

## Decision Points and Constraints
- Keep scope limited to recovery/stabilization for accidental-merge regressions.
- Do not remove intended P10 Web UI capabilities unless strictly required by failing tests and replaced with equivalent stable behavior.
- Prefer low-risk, minimal patches over structural rewrites.
- Preserve backward compatibility for documented CLI options and API payload contracts.

## Notes
After implementation completes, update workflow artifacts in sequence:
- Mark `P10-T3` complete in `SPECS/Workplan.md`.
- Archive PRD and validation report under `SPECS/ARCHIVE/P10-T3_Recover_Main_Branch_After_Accidental_Web_UI_Merge/`.
- Produce a structured review report and handle follow-up/archival steps per `SPECS/COMMANDS/FLOW.md`.

---
**Archived:** 2026-02-11
**Verdict:** PASS
