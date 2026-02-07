---
name: "commit"
description: "Use when the workflow requires creating a focused git commit for the current task with scoped staging and clear commit messages."
---

# COMMIT — Record Changes

**Version:** 1.0.0

## Purpose

Capture a focused snapshot of the mcpbridge-wrapper work so the tree reflects just the task at hand.

## Usage

```bash
$ git status -sb          # inspect staged vs unstaged files
$ git add <files…>        # stage only the files that belong to this PRD change
$ git commit -m "…short summary…"
```

## Guidelines

- Keep commits scoped to the current PRD or doc effort.
- Use a present-tense summary (e.g., `Implement bridge subprocess`, `Archive PRD`, `Add pytest configuration`). Use a verbose body only when extra context is necessary.
- When multiple commands manufacture a single deliverable (docs + code), prefer multiple commits so each change is reviewable.
- After committing, run `git status -sb` to confirm a clean worktree before pushing or archiving.

## Integration

Other commands (EXECUTE, ARCHIVE) rely on this primitive when they need a reliable snapshot. Pop the file whenever you want a quick reminder of the exact steps.
