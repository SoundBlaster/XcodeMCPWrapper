# mcpbridge-wrapper Workflow Commands

**Version:** 1.0.0

## Overview

This folder holds the command prompts that orchestrate the mcpbridge-wrapper documentation-driven workflow. Each command focuses on one phase:

| Command | Purpose | Reference |
|---------|---------|-----------|
| SELECT  | Pick the next task from the workplan | [SELECT.md](./SELECT.md) |
| PLAN    | Write the implementation PRD for the selected task | [PLAN.md](./PLAN.md) |
| EXECUTE | Run pre-flight/post-flight steps around your coding | [EXECUTE.md](./EXECUTE.md) |
| PROGRESS | Optional checkpointing inside `next.md` | [PROGRESS.md](./PROGRESS.md) |
| REVIEW  | Produce structured code reviews | [REVIEW.md](./REVIEW.md) |
| ARCHIVE | Move finished PRDs into `SPECS/ARCHIVE/` | [ARCHIVE.md](./ARCHIVE.md) |

Additional helpers live in `PRIMITIVES/` (toolchain, commits, doc updates, archive maintenance).
Main tasks tracker: `SPECS/Workplan.md`.
Task entry format: [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md).

## Workflow

```
SELECT → updates SPECS/INPROGRESS/next.md
 PLAN  → creates SPECS/INPROGRESS/{TASK}.md
EXECUTE → tests, linting, commits
             ↓
          ARCHIVE → moves completed PRDs into SPECS/ARCHIVE/
```

Running `PROGRESS` lets you keep `next.md` up to date during long tasks, while `REVIEW` provides independent quality checkpoints before or after merging.

## Structure

```
SPECS/
├── Workplan.md         # Main task tracker (this project)
├── ARCHIVE/            # Completed PRDs and specs
│   ├── INDEX.md        # Archive index
│   └── {TASK_ID}_{TASK_NAME}/  # Task-specific folder
│       ├── {TASK_ID}_{TASK_NAME}.md
│       └── {TASK_ID}_Validation_Report.md
├── INPROGRESS/         # Active task metadata and working PRDs
│   ├── next.md         # Current task summary
│   └── {TASK_ID}_{TASK_NAME}.md  # Detailed PRD per task
├── RULES/              # Writing rules (PRDs, reviews, etc.)
├── COMMANDS/           # This folder
│   ├── README.md
│   ├── SELECT.md
│   ├── PLAN.md
│   ├── EXECUTE.md
│   ├── PROGRESS.md
│   ├── REVIEW.md
│   ├── ARCHIVE.md
│   └── PRIMITIVES/     # Helper primitives
└── ...others…          # Documentation, etc.
```

## Quick Start

1. Run `SELECT` to choose the highest-priority task from `SPECS/Workplan.md` and write `SPECS/INPROGRESS/next.md` (task status/format in [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md)).
2. Run `PLAN` to produce the PRD in `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md`.
3. Run `EXECUTE` to follow the PRD, run tests/linting, and commit.
4. Repeat. When a task finishes, move it to `SPECS/ARCHIVE/` via ARCHIVE.

## Notes

- Keep `SPECS/INPROGRESS/` slim—only one task should be active at a time.
- Document completed work in `SPECS/ARCHIVE/` (PRDs stay for reference) and update `SPECS/Workplan.md` when needed, using [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md).
- This is a Python project (not Swift). Use pytest, ruff, and mypy for quality gates.
