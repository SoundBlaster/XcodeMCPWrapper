---
name: workplan-task-ops
description: Manage SPECS/Workplan.md task operations for this repository. Use when you need to add a new task entry with the canonical template, pick the next actionable task, or mark a task as completed while keeping selector state in sync.
---

# Workplan Task Ops

Manage task lifecycle operations in `SPECS/Workplan.md` using the repository conventions.

## Required Inputs

Collect these before running any operation:
- Target task ID (or task type and parent context if creating a new task)
- Target phase/backlog section in `SPECS/Workplan.md`
- Current status marker (`⬜️` open or `✅` completed)

Use these sources of truth:
- `SPECS/TASK_TEMPLATE.md` for task entry format and markers
- `SPECS/Workplan.md` for the actual task list
- `scripts/pick_next_task.py` for next-task selection and completion state updates

## Operation 1: Add Task

1. Determine task ID convention before editing:
- Phase task: `P{phase}-T{n}`
- Follow-up task: `FU-{parent/topic}-{n}`
- Bug task: `BUG-T{n}`

2. Place the task in the correct section of `SPECS/Workplan.md`.

3. Copy the open-task block from `SPECS/TASK_TEMPLATE.md` and fill all fields:
- Header with `⬜️` marker
- `Description`, `Priority`, `Dependencies`, `Parallelizable`
- `Outputs/Artifacts`
- `Acceptance Criteria` with unchecked boxes

4. Validate task entry quality:
- ID is unique in workplan
- Dependencies reference existing tasks or `none`
- Acceptance criteria are testable

## Operation 2: Pick Next Task

1. Run:
```bash
python3 scripts/pick_next_task.py
```

2. Read the suggested task and dependency statuses.

3. Confirm the suggestion is still open in `SPECS/Workplan.md` (`⬜️`) and not archived.

4. Update `SPECS/INPROGRESS/next.md` using the output template in `SPECS/COMMANDS/SELECT.md`.

## Operation 3: Mark Task Completed

1. Confirm completion evidence exists (implementation done, validation/review state consistent).

2. Update the task block in `SPECS/Workplan.md`:
- Change header marker from `⬜️` to `✅`
- Add or update `Status` line with date when applicable
- Check completed acceptance criteria (`[x]`)

3. Persist completion for selector state:
```bash
python3 scripts/pick_next_task.py --done <TASK_ID>
```

4. Verify follow-up selection:
```bash
python3 scripts/pick_next_task.py
```

## Guardrails

- Do not invent IDs that break existing conventions.
- Do not mark a task complete without matching acceptance evidence.
- Keep task formatting aligned with `SPECS/TASK_TEMPLATE.md`.
- Keep edits scoped to task-tracking files unless explicitly requested otherwise.
