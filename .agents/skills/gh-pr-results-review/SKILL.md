---
name: gh-pr-results-review
description: Review GitHub pull request CI outcomes with the GitHub CLI and extract actionable failure details from GitHub Actions logs. Use when asked to check failing PR checks, inspect lint/test/type-check errors, identify failing jobs, or summarize why a PR pipeline failed and what to fix first.
---

# GH PR Results Review

## Workflow

1. Identify the PR number and check status.
- Run:
```bash
gh pr checks <pr-number> 2>&1
```
- Capture failing checks, durations, run URL, and job URLs.
- If no failures exist, report success and stop.

2. Resolve run and failing job IDs.
- Derive the workflow run ID from the run URL when available.
- Derive each failing job ID from job URLs, or list jobs with:
```bash
gh run view <run-id> --json jobs
```

3. Pull logs for failed jobs.
- For each failed job:
```bash
gh run view <run-id> --job <job-id> --log 2>&1 | tail -80
```
- If the tail misses the error, inspect more lines or grep for error markers:
```bash
gh run view <run-id> --job <job-id> --log 2>&1 | rg -n "error|failed|traceback|E999|F401|mypy|pytest"
```

4. Summarize root causes with evidence.
- Report by failing check/job name.
- Include the shortest exact evidence line(s) that explain failure.
- State likely fix direction (for example: ruff import ordering, mypy type mismatch, failing pytest assertion).

## Output Format

Use this structure:

```text
check the CI failure details.

Reviewed GitHub Actions logs for test and linting results
Bash
gh pr checks <pr-number> 2>&1
<key failing checks output>

Bash
gh run view <run-id> --job <job-id> --log 2>&1 | tail -60
<relevant error/failure excerpt>

Bash
gh run view <run-id> --job <job-id> --log 2>&1 | tail -40
<relevant error/failure excerpt>
```

Then provide a short diagnosis section:
- `Finding`: one sentence per failed job.
- `Evidence`: command + key line.
- `Next fix`: concrete first edit to attempt.

## Guardrails

- Do not claim a job failed without a log line proving it.
- Prefer job-specific logs over workflow-level summaries.
- Keep excerpts tight; include only lines needed to justify the finding.
- If GitHub CLI lacks permission or run is missing, state the blocker and requested access explicitly.
