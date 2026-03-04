# P1-T5 PRD — Fix missed --broker-spawn references in troubleshooting

## Task Metadata
- **Task ID:** P1-T5
- **Phase:** Phase 1 — Documentation
- **Priority:** P2
- **Dependencies:** P1-T4
- **Source:** `SPECS/Workplan.md` open follow-up from P1-T4 review

## Objective Summary
Correct the two remaining stale `--broker-spawn` references in the `docs/troubleshooting.md` section titled "MCP tools are green, but dashboard is unreachable" so guidance is consistent with the broker-mode consolidation (`--broker`) completed in previous tasks. This task is intentionally narrow and should not alter runtime behavior, CLI parsing, or unrelated docs.

The change must align the docs source with existing guidance already reflected in the DocC mirror. The goal is to eliminate contradictory setup examples that could make users start a broker in a legacy mode when the project now documents `--broker` as the canonical entrypoint.

## Deliverables
- Updated `docs/troubleshooting.md` with both targeted command examples changed to `--broker --web-ui`.
- Validation report at `SPECS/INPROGRESS/P1-T5_Validation_Report.md` capturing quality gate outputs and verdict.
- Archived task artifacts after completion in `SPECS/ARCHIVE/P1-T5_Fix_missed_broker_spawn_references_in_troubleshooting/`.

## Success Criteria and Acceptance Tests
1. The line describing "only starts one when it must spawn a host" uses `--broker --web-ui`.
2. The "Unified broker single-config" solution option uses `--broker --web-ui`.
3. `make doccheck-all` passes to confirm docs and DocC mirrors stay synchronized.
4. Required FLOW quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`) complete successfully with coverage at or above 90%.

## Test-First Plan
1. Identify current failing condition by searching for `--broker-spawn --web-ui` in `docs/troubleshooting.md` and confirming exactly two target hits in the impacted section.
2. Confirm mirror baseline by checking the corresponding DocC troubleshooting content is already on `--broker` (no edit expected there).
3. Apply minimal text edits in the docs source only.
4. Re-run search to assert no stale `--broker-spawn` remains in that section.

## Hierarchical Execution Plan

### Phase A — Baseline and scope lock
- **Inputs:** `SPECS/Workplan.md`, `docs/troubleshooting.md`, DocC troubleshooting mirror.
- **Outputs:** Confirmed exact edit scope (2 lines).
- **Verification:** `rg -n "broker-spawn|MCP tools are green" docs/troubleshooting.md` and targeted mirror spot-check.

### Phase B — Documentation correction
- **Inputs:** Baseline findings from Phase A.
- **Outputs:** `docs/troubleshooting.md` updated from `--broker-spawn --web-ui` to `--broker --web-ui` in the two required lines.
- **Verification:** `git diff -- docs/troubleshooting.md` shows only expected replacements.

### Phase C — Validation and reporting
- **Inputs:** Edited docs + repo quality gates.
- **Outputs:** Passing validation commands and `SPECS/INPROGRESS/P1-T5_Validation_Report.md`.
- **Verification:** Command exit codes are zero; coverage output reports >=90%; report records PASS/FAIL/PARTIAL clearly.

## Decision Points and Constraints
- Keep edits minimal and task-scoped; avoid opportunistic rewrites.
- Preserve existing wording and structure except for command flag correction.
- If `make doccheck-all` surfaces unrelated failures, record them explicitly and classify verdict accordingly.

## Notes
- After EXECUTE, archive using the ARCHIVE command workflow and mark P1-T5 as completed in `SPECS/Workplan.md`.
- If review finds no new issues, FOLLOW-UP is skipped and REVIEW artifact is archived immediately.
