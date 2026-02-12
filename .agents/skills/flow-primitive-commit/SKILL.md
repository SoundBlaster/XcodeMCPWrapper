---
name: flow-primitive-commit
description: Create focused, scoped git commits for the current task. Use when the workflow requires committing work, when only specific files should be staged, when commit messages must be clear and present-tense, or when validating the worktree state before push/archive.
---

# Flow Primitive Commit

Create a reliable commit snapshot that includes only files relevant to the active task.

## Workflow

1. Inspect status:

```bash
git status -sb
```

2. Stage only task-relevant files:

```bash
git add <files...>
```

3. Commit with a concise present-tense summary:

```bash
git commit -m "Add Web UI release task to workplan"
```

4. Verify post-commit state:

```bash
git status -sb
```

## Rules

- Keep commits scoped to one task/PRD change.
- Prefer explicit file staging over `git add .`.
- Use present-tense commit subjects.
- Split mixed deliverables into multiple commits when reviewability improves.
- Do not amend or rewrite history unless explicitly requested.
