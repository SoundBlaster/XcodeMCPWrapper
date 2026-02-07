# PROGRESS — Record Intermediate Checkpoints

**Version:** 1.0.0

## Purpose

PROGRESS keeps `SPECS/INPROGRESS/next.md` aligned with what you are currently doing. It is typically invoked during long-running tasks to tick off mini steps without touching the PRD.

## Inputs

- `SPECS/INPROGRESS/next.md` — current task.
- Optional: the active PRD for reference.

## Process

1. Open `SPECS/INPROGRESS/next.md` and add a short checklist under a ## Progress section if not already present.
2. Mark items like `- [x] Set up pytest config`, `- [ ] Write bridge tests` to reflect actual work.
3. Use PROGRESS only for short-lived notes; don't recreate the PRD inside it.
4. If the task finishes, leave PROGRESS untouched — ARCHIVE will move the PRD and you can remove `next.md` with SELECT later.

## Output

- Updated `SPECS/INPROGRESS/next.md` with a mini checklist (optional).

## Guidelines

- PROGRESS is run manually when you need a quick checkpoint; it is not required for every change.
- Keep the summary bullet list short (3-5 items) and delete the section once the task finishes.
