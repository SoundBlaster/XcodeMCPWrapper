# SELECT — Next Task Selection

**Version:** 1.0.0

## Purpose

Choose the next mcpbridge-wrapper task to work on without re-planning. SELECT keeps the "current task" file minimal so the PLAN command can create the detailed PRD.

## Inputs

- `SPECS/Workplan.md` as the main tasks tracker (phases, priorities, status).
- [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md) as the canonical task status/entry format.
- `SPECS/INPROGRESS/next.md` (if it exists) to round out what is already active.
- Notes in `AGENTS.md` for related constraints.

## Algorithm

1. Gather outstanding items from `SPECS/Workplan.md` using status markers defined in [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md). Assign each a priority tag (P0, P1, P2) and note dependencies.
2. Filter candidates to those:
   - Not marked complete in the workplan.
   - Dependencies already satisfied or documented with blocking tasks.
   - Central to current phase (critical path first).
3. If multiple candidates remain, prefer (in order): P0 > P1 > P2, then the one with the least outstanding blockers, then the most urgent milestone.
4. Write `SPECS/INPROGRESS/next.md` with only the metadata below (no implementation details).
5. Highlight the selected task in the workplan by appending `**INPROGRESS**` or similar marker.

Alternatively, use the helper script:
```bash
python scripts/pick_next_task.py
```

## Output (`SPECS/INPROGRESS/next.md` template)

```markdown
# Next Task: {TASK_ID} — {Task Name}

**Priority:** P{0/1/2}
**Phase:** {Phase or module}
**Effort:** {Hours}
**Dependencies:** {IDs or "None"}
**Status:** Selected

## Description

{Brief summary pulled from the workplan.}

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
```

## Guidelines

- Keep `next.md` slim; no checklists, acceptance criteria, or code samples.
- Always reference the workplan entry so reviewers understand why this task was chosen.
- If no candidates exist, report that the workplan is empty (and consider adding new entries in `SPECS/Workplan.md` using [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md)).
