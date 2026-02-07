# ARCHIVE — Archive Completed Tasks

**Version:** 1.0.0

## Purpose

Scan for completed tasks and archive them from `SPECS/INPROGRESS/` to `SPECS/ARCHIVE/`.

## Inputs

- `SPECS/Workplan.md` — roadmap with task status
- `SPECS/INPROGRESS/next.md` — current task pointer
- `SPECS/INPROGRESS/{TASK_ID}_*.md` — task files to archive

## Algorithm

1. **Scan for completed tasks** in workplan:
   - Check validation report exists with PASS/FAIL/PARTIAL verdict
   - Confirm all deliverables are addressed

2. **For each completed task:**
   - Execute [`ARCHIVE_TASK`](PRIMITIVES/ARCHIVE_TASK.md) primitive with:
     - `TASK_ID` — task identifier (e.g., `P1-T1`)
     - `TASK_NAME` — task name
     - `VERDICT` — from validation report
     - `DATE` — current date
   - When updating `SPECS/ARCHIVE/INDEX.md`, preserve the Archive Log header separator row directly beneath the header.

3. **Update `SPECS/INPROGRESS/next.md`:**
   - Clear current task block
   - Add entry to "Recently Archived" section
   - Suggest next tasks from workplan

4. **For non-task artifacts** (code reviews, reports):
   ```bash
   mkdir -p "SPECS/ARCHIVE/_Historical"
   mv "SPECS/INPROGRESS/{artifact}.md" "SPECS/ARCHIVE/_Historical/"
   ```
   - Add entry to Historical Artifacts table in INDEX.md

5. **Commit** via `COMMIT` primitive if desired.

## Modes

| Mode | Description |
|------|-------------|
| **Auto** | Archive all completed tasks |
| **Single `{TASK_ID}`** | Archive only specified task |
| **Dry run** | Report without modifying files |

## Archive Structure

```
SPECS/
├── ARCHIVE/
│   ├── INDEX.md
│   ├── {TASK_ID}_{TASK_NAME}/
│   │   ├── {TASK_ID}_{TASK_NAME}.md
│   │   └── {TASK_ID}_Validation_Report.md
│   └── _Historical/
└── INPROGRESS/
    └── next.md
```

## INDEX.md Format

```markdown
# mcpbridge-wrapper Tasks Archive

**Last Updated:** YYYY-MM-DD

## Archived Tasks

| Task ID | Folder | Archived | Verdict |
|---------|--------|----------|---------|

## Historical Artifacts

| Folder | Description |
|--------|-------------|
| [_Historical/](_Historical/) | Non-task artifacts |

## Archive Log

| Date | Task ID | Action |
|------|---------|--------|
```

## Example Output

```
ARCHIVE: Scanning for completed tasks...

Found 1 completed task: P1-T1_Create_Project_Structure
  → Executing ARCHIVE_TASK primitive
  ✓ Archived to SPECS/ARCHIVE/P1-T1_Create_Project_Structure/

Updated SPECS/INPROGRESS/next.md

ARCHIVE complete: 1 task archived
```
