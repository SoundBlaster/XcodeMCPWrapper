# FLOW — mcpbridge-wrapper Documentation Workflow

**Version:** 1.0.0

## Overview

mcpbridge-wrapper uses a documentation-driven workflow: select a task, plan it fully, execute with validations, and archive the PRD when done. Each major step ends with a commit.

```
BRANCH → SELECT → PLAN → EXECUTE → ARCHIVE → REVIEW → FOLLOW-UP → ARCHIVE-REVIEW
   ↓        ↓       ↓        ↓         ↓         ↓          ↓             ↓
 COMMIT   COMMIT  COMMIT   COMMIT    COMMIT    COMMIT     COMMIT        COMMIT
```

---

## Changelog

- 1.0.0 — Initial Python project workflow (adapted from Puzzle Framework workflow)

---

## Steps

### 1. BRANCH

Create a new feature branch from `main` for the task.

**Actions:**
- Ensure you're on main: `git checkout main`
- Pull latest changes: `git pull origin main`
- Create feature branch: `git checkout -b feature/{TASK_ID}-{short-description}`

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Branch for {TASK_ID}: {short description}
```

---

### 2. SELECT

Choose the next task from the workplan.

**Actions:**
- Read `SPECS/Workplan.md` for available tasks
- Run `python scripts/pick_next_task.py` or manually select
- Update `SPECS/INPROGRESS/next.md` with chosen task metadata

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Select task {TASK_ID}: {TASK_NAME}
```

---

### 3. PLAN

Create the task PRD following documentation rules.

**Actions:**
- Create `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md`
- Define deliverables, acceptance criteria, dependencies

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Plan task {TASK_ID}: {TASK_NAME}
```

---

### 4. EXECUTE

Implement the task per the PRD.

**Actions:**
- Implement code changes per PRD specifications
- Run quality gates:
  - `pytest` — all tests pass
  - `ruff check src/` — no linting errors
  - `mypy src/` — type checking (if configured)
  - `pytest --cov` — coverage ≥90%
- Create validation report: `SPECS/INPROGRESS/{TASK_ID}_Validation_Report.md`

See [`EXECUTE`](EXECUTE.md) for detailed quality gate documentation.

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Implement {TASK_ID}: {brief description of changes}
```

*Note: For large tasks, commit incrementally after each logical unit of work.*

---

### 5. ARCHIVE

Move completed task to archive (run periodically or at milestones).

**Actions:**
- Execute [`ARCHIVE`](ARCHIVE.md) command
- Verify task moved to `SPECS/ARCHIVE/{TASK_ID}_{TASK_NAME}/`
- Confirm `next.md` updated
- Mark task as ✅ in `SPECS/Workplan.md`

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Archive task {TASK_ID}: {TASK_NAME} ({VERDICT})
```

---

### 6. REVIEW

Run a structured review after archiving to capture findings and follow-ups.

**Actions:**
- Execute [`REVIEW`](REVIEW.md)
- Save report under `SPECS/INPROGRESS/` as `REVIEW_{subject}.md`

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Review {TASK_ID}: {short subject}
```

---

### 7. FOLLOW-UP

Create subtasks for issues discovered during review.

**Actions:**
- Execute [`FOLLOW_UP`](PRIMITIVES/FOLLOW_UP.md) command
- Add new tasks to `SPECS/Workplan.md` for actionable items

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Follow-up {TASK_ID}: {short subject}
```

*Note: Skip this step if review found no actionable issues.*

---

### 8. ARCHIVE-REVIEW

Archive the REVIEW artifact after FOLLOW-UP is complete.

**Actions:**
- Move `REVIEW_{subject}.md` to `SPECS/ARCHIVE/_Historical/` (or the relevant task folder)
- Update `SPECS/ARCHIVE/INDEX.md`

**Commit via [`COMMIT`](PRIMITIVES/COMMIT.md):**
```
Archive REVIEW_{subject} report
```

*Note: If FOLLOW-UP is skipped, archive the review immediately after REVIEW.*

## Quick Reference

| Step | Output | Commit Message Pattern |
|------|--------|------------------------|
| BRANCH | Feature branch created | `Branch for {TASK_ID}: {short description}` |
| SELECT | `next.md` updated | `Select task {TASK_ID}: {TASK_NAME}` |
| PLAN | `{TASK_ID}_{TASK_NAME}.md` created | `Plan task {TASK_ID}: {TASK_NAME}` |
| EXECUTE | Code + validation report | `Implement {TASK_ID}: {DESCRIPTION}` |
| ARCHIVE | Task in archive folder + workplan updated | `Archive task {TASK_ID}: {TASK_NAME} ({VERDICT})` |
| REVIEW | `REVIEW_{subject}.md` created | `Review {TASK_ID}: {SUBJECT}` |
| FOLLOW-UP | New tasks in workplan | `Follow-up {TASK_ID}: {SUBJECT}` |
| ARCHIVE-REVIEW | Review report archived | `Archive REVIEW_{subject} report` |

## Extensions

- **PROGRESS** — Note temporary checkpoints inside `next.md`
- **Primitives** — See `SPECS/COMMANDS/PRIMITIVES/` for helper steps
- **Workflow** — `SPECS/Workplan.md` is the master task tracker
