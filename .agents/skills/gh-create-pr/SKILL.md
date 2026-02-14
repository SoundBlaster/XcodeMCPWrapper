---
name: gh-create-pr
description: Create or update GitHub pull requests with the GitHub CLI (`gh`) using the repository PR template. Use when asked to open a PR, fix PR description formatting, align description with `.github/PULL_REQUEST_TEMPLATE.md`, or prepare a merge-ready PR with validation results.
---

# GH Create PR

## Workflow

1. Confirm branch and working tree are ready.
- Run `git status -sb`.
- Ensure commits are complete and branch is pushed.

2. Collect PR context.
- Read `.github/PULL_REQUEST_TEMPLATE.md` when present.
- Gather summary of changes and executed checks from commits and task artifacts.
- Prefer factual check results and avoid claiming manual tests that were not run.

3. Create or update PR with `gh`.
- Create:
```bash
gh pr create --base main --head <branch> --title "<title>" --body-file <body.md>
```
- Update existing PR description:
```bash
gh pr edit <number-or-url> --body-file <body.md>
```

4. Use template-accurate checkboxes.
- Mark only items that were actually completed.
- Leave unchecked items for unperformed steps.
- Keep wording from the template unchanged; only fill values/check states.

5. Verify PR state.
- Open or print PR URL from `gh` output.
- Optionally run:
```bash
gh pr view <number-or-url> --json number,title,url,headRefName,baseRefName
```

## Body Authoring Rules

- Keep description short and concrete.
- Include changed areas, bug/task ID when available, and validation commands.
- Mention warnings or non-blocking caveats if present.
- Do not include markdown sections not in the template when template compliance is requested.

## Fast Patterns

Template-first PR update:
1. Read template.
2. Create `body.md` following the exact headings/order.
3. Apply with `gh pr edit <pr> --body-file body.md`.

New PR from current branch:
1. Build `body.md` from template.
2. Run `gh pr create --base main --head $(git branch --show-current) ...`.
