# FU-P9-T4-1 — Align publish_helper output with protected main branch workflow

**Priority:** P1  
**Dependencies:** P9-T4  
**Phase:** Phase 9 Follow-up Backlog

## Objective
Ensure release guidance emitted by `scripts/publish_helper.py` is safe for repositories where `main` is protected and direct push is disallowed.

## Deliverables
1. Update the helper summary command block to a PR-first flow:
   - create release branch
   - commit and push release branch
   - open/merge PR into `main`
   - pull `main`, then create and push tag
2. Update unit tests in `tests/unit/test_publish_helper.py` to assert protected-branch-safe guidance is printed.
3. Keep current helper behavior unchanged for version updates themselves (only guidance text/commands should change).
4. Produce validation evidence in `SPECS/INPROGRESS/FU-P9-T4-1_Validation_Report.md`.

## Acceptance Criteria
1. Running `python scripts/publish_helper.py <version>` does not suggest direct push-to-main flow.
2. Printed commands include branch creation/push and explicit PR-merge step before tagging.
3. Guidance still includes tag creation/push after merge to trigger publish workflow.
4. `pytest tests/unit/test_publish_helper.py` passes.

## Execution Plan
1. Modify `print_summary()` command output in `scripts/publish_helper.py`.
2. Update test assertions to match new guidance text.
3. Run required quality gates per FLOW:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov` (>= 90%)
4. Write validation report with acceptance criteria and gate outputs.
