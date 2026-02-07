# PLAN — Generate an Implementation PRD

**Version:** 1.0.0

## Purpose

PLAN turns the selected task into a self-contained, implementation-ready PRD inside `SPECS/INPROGRESS/`. It follows the structure defined in the workplan and keeps all execution details in one document for the EXECUTE command to follow.

## Inputs

- `SPECS/INPROGRESS/next.md` — current task metadata chosen by SELECT.
- `SPECS/Workplan.md` for workplan context (phase, references, dependencies).

## Process

1. Create `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md` (title-cased, underscores instead of spaces). Copy the high-level statements from `next.md` and amplify them with:
   - A short objective summary
   - Success criteria and acceptance tests
   - A test-first plan (tests to write before any implementation changes)
   - A hierarchical TODO plan (at least 3 phases or subtasks)
   - Any decision points, platform constraints, or toolchain requirements
2. Each subtask must have inputs, outputs, and verification steps. Use tables, bullet lists, or numbered steps for clarity.
3. Include a "Notes" section for docs to update once the task is complete.
4. Keep the PRD concise (200–400 words per major section) but detailed enough that someone following it never needs additional clarification.
5. Save the PRD and update `SPECS/Workplan.md` if the task status or references need a note.

## Output

- `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md` containing the plan.
- `SPECS/INPROGRESS/next.md` still references the task but can stay minimal; no changes needed unless metadata updates are required.

## Notes

- Do not mix multiple tasks inside a single PRD; split them into separate files when you have multiple independent deliverables.
- When the PRD is complete, feed it to EXECUTE, which will display it before you start coding.
