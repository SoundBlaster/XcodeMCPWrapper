# P1-T9 - Add direct links for all command steps in FLOW.md

**Task ID:** P1-T9
**Priority:** P2
**Dependencies:** none
**Status:** Planned

## Goal

Make `SPECS/COMMANDS/FLOW.md` directly navigable by adding explicit links to every command-backed step in the workflow.

## Problem Statement

`SPECS/COMMANDS/FLOW.md` describes the workflow sequence and names commands such as PLAN, EXECUTE, ARCHIVE, REVIEW, and FOLLOW-UP, but navigation is inconsistent because some steps are not directly linked to their command documents from the step sections. This slows task execution and increases the chance of missing step-specific guidance.

## Deliverables

- `SPECS/COMMANDS/FLOW.md`
  - Add direct links for command-backed steps in the step sections.
  - Ensure PLAN step links to `PLAN.md` directly.
  - Keep wording and quick reference consistent with the linked step names.

## Acceptance Criteria

- Each command-backed step section in `SPECS/COMMANDS/FLOW.md` includes a direct markdown link to its command file.
- PLAN step includes a direct link to `PLAN.md`.
- Existing links remain valid after edits.
- Required quality gates pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` (>=90%)

## Implementation Notes

- Use repository-relative links matching neighboring command docs (for example, `PLAN.md`, `EXECUTE.md`, `ARCHIVE.md`, `REVIEW.md`, `PRIMITIVES/FOLLOW_UP.md`).
- Keep the workflow sequence and commit message patterns unchanged.
- Avoid broad formatting churn in `FLOW.md`; keep this task focused on link coverage and clarity.

## Validation Plan

1. Inspect `SPECS/COMMANDS/FLOW.md` to confirm direct links exist for each command-backed step.
2. Run required quality gates.
3. Create `SPECS/INPROGRESS/P1-T9_Validation_Report.md` with command outcomes and final verdict.

## Risks

- Over-editing wording could accidentally drift from established FLOW semantics.

## Out of Scope

- Changing workflow order or commit message patterns.
- Editing command-specific behavior in files other than `SPECS/COMMANDS/FLOW.md`.
