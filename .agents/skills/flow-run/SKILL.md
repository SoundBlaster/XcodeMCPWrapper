---
name: flow-run
description: Run the complete task workflow for this repository by strictly following SPECS/COMMANDS/FLOW.md from BRANCH through ARCHIVE-REVIEW, including required commit checkpoints and quality gates. Use when asked to do the next task end-to-end, complete the full workflow, or execute "start to finish" task delivery in this project.
---

# Flow Run

Execute the workflow in `SPECS/COMMANDS/FLOW.md` exactly, without skipping required steps unless the workflow itself explicitly allows skipping.

## Required Inputs

Collect these before starting:
- Task identifier (for example `P5-T2`) and short description.
- Current branch and whether a feature branch already exists.
- Confirmation of which review subject name to use for `REVIEW_{subject}.md`.

If the task identifier is unknown, determine it from `SPECS/Workplan.md` and `SPECS/INPROGRESS/next.md` during SELECT.

## Execution Contract

Apply these rules throughout execution:
- Read `SPECS/COMMANDS/FLOW.md` at the beginning and treat it as the source of truth.
- Complete steps in order: `BRANCH -> SELECT -> PLAN -> EXECUTE -> ARCHIVE -> REVIEW -> FOLLOW-UP -> ARCHIVE-REVIEW -> PR`.
- Use the `flow-primitive-commit` skill for every commit checkpoint — stage only task-relevant files and use present-tense FLOW message patterns.
- Run required quality gates during EXECUTE (`pytest`, `ruff check src/`, `mypy src/` if configured, `pytest --cov` with coverage >= 90%).
- Record artifacts in expected locations under `SPECS/INPROGRESS/` and `SPECS/ARCHIVE/`.
- If REVIEW has no actionable issues, skip FOLLOW-UP and proceed directly to ARCHIVE-REVIEW, as FLOW permits.
- After ARCHIVE-REVIEW, use the `gh-create-pr` skill to open a pull request from the feature branch into `main`.

## Step Procedure

1. BRANCH
- Ensure `main` is up to date.
- Create `feature/{TASK_ID}-{short-description}` if not already on the correct feature branch.
- Use `flow-primitive-commit` skill — commit message pattern: `Branch for {TASK_ID}: {short description}`.

2. SELECT
- Choose the next task from `SPECS/Workplan.md` (optionally with `python scripts/pick_next_task.py`).
- Update `SPECS/INPROGRESS/next.md` with selected task metadata.
- Use `flow-primitive-commit` skill — commit message pattern: `Select task {TASK_ID}: {TASK_NAME}`.

3. PLAN
- Create the task PRD at `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md`.
- Define deliverables, acceptance criteria, dependencies.
- Use `flow-primitive-commit` skill — commit message pattern: `Plan task {TASK_ID}: {TASK_NAME}`.

4. EXECUTE
- Implement to the PRD.
- Run quality gates defined in FLOW.
- Create `SPECS/INPROGRESS/{TASK_ID}_Validation_Report.md`.
- Use `flow-primitive-commit` skill — commit message pattern: `Implement {TASK_ID}: {brief description of changes}`.
- For large tasks, invoke `flow-primitive-commit` incrementally after each logical unit of work.

5. ARCHIVE
- Run `SPECS/COMMANDS/ARCHIVE.md` workflow.
- Verify task archive folder exists under `SPECS/ARCHIVE/{TASK_ID}_{TASK_NAME}/`.
- Confirm `SPECS/INPROGRESS/next.md` and `SPECS/Workplan.md` are updated.
- Use `flow-primitive-commit` skill — commit message pattern: `Archive task {TASK_ID}: {TASK_NAME} ({VERDICT})`.

6. REVIEW
- Run `SPECS/COMMANDS/REVIEW.md`.
- Save review report at `SPECS/INPROGRESS/REVIEW_{subject}.md`.
- Use `flow-primitive-commit` skill — commit message pattern: `Review {TASK_ID}: {short subject}`.

7. FOLLOW-UP
- If review has actionable findings, run `SPECS/COMMANDS/PRIMITIVES/FOLLOW_UP.md`.
- Add follow-up tasks to `SPECS/Workplan.md`.
- Use `flow-primitive-commit` skill — commit message pattern: `Follow-up {TASK_ID}: {short subject}`.
- If no actionable findings, explicitly note FOLLOW-UP skipped.

8. ARCHIVE-REVIEW
- Move `REVIEW_{subject}.md` to `SPECS/ARCHIVE/_Historical/` or relevant task folder.
- Update `SPECS/ARCHIVE/INDEX.md`.
- Use `flow-primitive-commit` skill — commit message pattern: `Archive REVIEW_{subject} report`.

9. PR
- Use `gh-create-pr` skill to open a pull request from the feature branch into `main`.
- Title: `{TASK_ID}: {TASK_NAME}`.
- Body: summarise changes, list quality gate results, reference the validation report.

## Completion Criteria

Consider the run complete only when all are true:
- FLOW step sequence has been fully executed (or optional FOLLOW-UP formally skipped due to no findings).
- Required artifacts exist in `SPECS/INPROGRESS/` and/or `SPECS/ARCHIVE/`.
- Required quality gates were run and outcomes captured.
- Every commit checkpoint was created via the `flow-primitive-commit` skill with FLOW message patterns.
- A pull request from the feature branch into `main` was opened via the `gh-create-pr` skill.

## Trigger Phrases

Use this skill when requests look like:
- "Do the next task from start to end."
- "Run the full FLOW workflow for the next task."
- "Take this task all the way through branch, plan, execute, archive, and review."
- "Strictly follow the instructions in the @SPECS/COMMANDS/FLOW.md file carefully for the next task. Do not stop between steps. Complete each phase of the FLOW process one by one without asking questions or pausing."
