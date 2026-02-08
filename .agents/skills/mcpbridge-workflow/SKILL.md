---
name: mcpbridge-workflow
description: |
  Task tracking and workflow management for the mcpbridge-wrapper project.
  Use when working on mcpbridge-wrapper to: (1) Get the next task to work on,
  (2) Mark tasks as completed, (3) View project progress, (4) List available tasks.
  The workplan is stored in SPECS/Workplan.md with 65 tasks across 7 phases.
  Task state is persisted in .task_state.json.
---

# mcpbridge-workflow

Task tracking for the mcpbridge-wrapper project development.

## Quick Start

Get the next task:
```bash
python3 scripts/pick_next_task.py
```

Mark a task done:
```bash
python3 scripts/pick_next_task.py --done P1-T1
```

Show progress:
```bash
python3 scripts/pick_next_task.py --progress
# Or use calc_progress.py for different output formats:
python3 scripts/calc_progress.py --markdown
```

List all tasks:
```bash
python3 scripts/pick_next_task.py --list
```

## Workplan Structure

The workplan at `SPECS/Workplan.md` contains 66 tasks across 8 phases.

**When to read the full workplan:**
- Before starting work on a task (to see full acceptance criteria)
- To understand task dependencies in detail
- To review the dependency graph or traceability matrix

For task format details, see [references/task-format.md](references/task-format.md).

| Phase | Focus | Tasks | P0 Tasks |
|-------|-------|-------|----------|
| 1 | Foundation & Scaffolding | 6 | 3 |
| 2 | Core Bridge Implementation | 7 | 4 |
| 3 | Response Transformation Engine | 10 | 8 |
| 4 | Edge Case Handling | 9 | 0 |
| 5 | Testing & Verification | 14 | 8 |
| 6 | Packaging & Distribution | 8 | 3 |
| 7 | Documentation | 11 | 3 |

Task IDs follow the pattern `P{phase}-T{task}` (e.g., `P1-T1`, `P3-T5`).

## Priority Levels

- **P0**: Must complete for MVP (critical path)
- **P1**: Should complete (important but not blocking)
- **P2**: Nice to have (polish and enhancements)
- **P3**: Future work (post-MVP)

## Scripts

Two scripts are available for task management:

### pick_next_task.py
Main task tracker with state persistence.

**Location:** `scripts/pick_next_task.py`

### calc_progress.py
Calculate and display progress from workplan (no state tracking).

**Location:** `scripts/calc_progress.py`

**Additional options:**
```bash
python3 scripts/calc_progress.py --json       # JSON output
python3 scripts/calc_progress.py --markdown   # Markdown table
python3 scripts/calc_progress.py --todo       # Pending tasks only
python3 scripts/calc_progress.py --phase P1   # Phase 1 tasks
```

### Default: Show Next Task

Without arguments, shows the highest-priority available task with unmet dependencies:

```bash
python3 scripts/pick_next_task.py
```

Output includes:
- Task ID and description
- Phase and priority
- Dependency status (done/pending)
- Acceptance criteria
- Overall progress

### Mark Task Complete

```bash
python3 scripts/pick_next_task.py --done TASK_ID
```

Example:
```bash
python3 scripts/pick_next_task.py --done P1-T1
```

Validates task ID exists in workplan before saving.

### Show Progress

```bash
python3 scripts/pick_next_task.py --progress
```

Displays progress bars for each phase and P0 task completion counts.

### List Tasks

```bash
python3 scripts/pick_next_task.py --list
python3 scripts/pick_next_task.py --list --phase 1
```

Shows all tasks with status (DONE/TODO) and blocking indicators.

## Task Selection Logic

Tasks are selected based on:

1. **All dependencies complete** - Task is available
2. **Phase order** - Earlier phases take precedence
3. **Priority** - P0 before P1 before P2 before P3
4. **Task ID** - Alphabetical for tie-breaking

Blocked tasks (incomplete dependencies) are shown with `[BLOCKED]`.

## State Files

- `.task_state.json` - Completed task IDs
- `.current_task` - Current task suggestion (updated by script)

Both are gitignored.

## Working a Task

1. Get the next task:
   ```bash
   python3 scripts/pick_next_task.py
   ```

2. Read the full task details in `SPECS/Workplan.md`

3. Implement the task

4. Run tests to verify:
   ```bash
   python3 -m pytest tests/ -v
   ```

5. Mark complete:
   ```bash
   python3 scripts/pick_next_task.py --done P1-T1
   ```

6. Commit with message referencing task ID:
   ```bash
   git add .
   git commit -m "P1-T1: Create project directory structure"
   ```

## Completion Criteria

Project is complete when:
- All P0 tasks: 100% complete
- All P1 tasks: ≥80% complete
- Test coverage: ≥90%
- All 20 Xcode MCP tools verified (P5-T13)
- Overhead <5ms verified (P5-T11)
