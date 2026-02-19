# Workplan Task Template

Canonical template for adding tasks to `/Users/egor/Development/GitHub/XcodeMCPWrapper/SPECS/Workplan.md`.

## Status Markers

- `⬜️` = open task (not completed)
- `✅` = completed task

Use the marker at the start of the task header (preferred), for example:

```markdown
#### ⬜️ P12-T4: Implement example task
```

## Task ID Conventions

- Phase task: `P{PHASE}-T{N}` (example: `P12-T4`)
- Follow-up task: `FU-{PARENT_OR_TOPIC}-{N}` (example: `FU-P12-T1-5`)
- Bug task: `BUG-T{N}` (example: `BUG-T8`)
- Rebuild task: `REBUILD-{TOPIC}` (example: `REBUILD-P10-T1`)

## Open Task Template

```markdown
#### ⬜️ {TASK_ID}: {TASK_NAME}
- **Description:** {What must be done and why}
- **Priority:** P0|P1|P2|P3
- **Dependencies:** none|{TASK_ID_1}, {TASK_ID_2}
- **Parallelizable:** yes|no
- **Outputs/Artifacts:**
  - {File/path/output 1}
  - {File/path/output 2}
- **Acceptance Criteria:**
  - [ ] {Verifiable outcome 1}
  - [ ] {Verifiable outcome 2}
```

## Completed Task Template

Use this when archiving/marking a task complete:

```markdown
#### ✅ {TASK_ID}: {TASK_NAME}
- **Status:** ✅ Completed ({YYYY-MM-DD})
- **Description:** {What was implemented}
- **Priority:** P0|P1|P2|P3
- **Dependencies:** none|{TASK_ID_1}, {TASK_ID_2}
- **Parallelizable:** yes|no
- **Outputs/Artifacts:**
  - {Delivered artifact 1}
  - {Delivered artifact 2}
- **Acceptance Criteria:**
  - [x] {Satisfied criterion 1}
  - [x] {Satisfied criterion 2}
```

## Notes

- Keep task headers unique by ID.
- Prefer explicit dependencies (`none` or comma-separated IDs).
- Use checklist items in acceptance criteria so verification is unambiguous.
