# Task Format Reference

Quick reference for parsing and understanding tasks in SPECS/Workplan.md.

## Task ID Format

Tasks follow the pattern: `P{phase}-T{task_number}`

Examples:
- `P1-T1` - Phase 1, Task 1
- `P3-T5` - Phase 3, Task 5
- `P7-T11` - Phase 7, Task 11

## Task Structure

Each task in the workplan uses this markdown format:

```markdown
#### P1-T1: Task Title Here
- **Description:** Detailed description of what the task involves
- **Priority:** P0 | P1 | P2 | P3
- **Dependencies:** P1-T1, P1-T2 | none
- **Parallelizable:** yes | no
- **Outputs/Artifacts:** 
  - List of files to create
  - Or artifacts produced
- **Acceptance Criteria:** Specific criteria to mark task complete
```

## Priority Levels

| Level | Name | Description |
|-------|------|-------------|
| P0 | Critical | Must complete for MVP (critical path) |
| P1 | Important | Should complete (important but not blocking) |
| P2 | Nice to have | Polish and enhancements |
| P3 | Future work | Post-MVP or stretch goals |

## Parsing Tasks

When parsing the workplan:

1. **Find phases** - Look for `### Phase {N}:` headers
2. **Find tasks** - Within each phase, look for `#### {P{N}-T{N}}:` headers
3. **Extract fields** - Parse bullet points after the task header
4. **Stop condition** - Next task header (`#### `) or next phase (`### `)

## State Persistence

Task completion state is stored in `.task_state.json`:

```json
{
  "completed": ["P1-T1", "P1-T2", "P2-T1"]
}
```

Current task suggestion is cached in `.current_task` for reference.
