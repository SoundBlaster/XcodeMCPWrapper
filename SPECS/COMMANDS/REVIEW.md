# REVIEW — Structured Code Review

**Version:** 1.0.0

## Purpose

Apply a structured code review to any set of commits or staged changes. This command produces a thorough review report suitable for sharing with peers or pasting into a PR comment.

## Inputs

- Current git branch (commits since `main`/`origin/main`) or any explicit commit range
- Related PRD or workplan for context (from `SPECS/INPROGRESS` or `SPECS/Workplan.md`)

## Algorithm

1. **Define scope**
   - Branch review: `git log --oneline origin/main..HEAD`
   - Commit range: `git log --oneline abc..def`
   - Staged diff: `git diff --cached`

2. **Gather context**
   - Identify the active PRD in `SPECS/INPROGRESS` associated with the changes.
   - Note architectural contracts and intended behaviors described in the PRD.

3. **Apply the Code Review checklist**:
   - Correctness & logic
   - Architecture & design
   - Maintainability & readability
   - Performance & resource usage (<5ms latency, <10MB memory per NFRs)
   - Security & safety
   - Concurrency/state (if applicable)

4. **Classify findings** by severity: Blocker, High, Medium, Low, Nit.

5. **Document results** in `SPECS/INPROGRESS/REVIEW_{subject}.md` (e.g., `REVIEW_bridge_subprocess.md`) following this template:

```markdown
## REVIEW REPORT — {Subject}

**Scope:** origin/main..HEAD
**Files:** {count}

### Summary Verdict
- [ ] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues
- [Blocker/High] description + fix suggestion

### Secondary Issues
- [Medium/Low] description + fix suggestion

### Architectural Notes
- Observations that affect future work

### Tests
- Mention affected or missing tests
- Check coverage remains ≥90%

### Next Steps
- Follow-up actions, docs to update, etc.
```

6. **Create backlog tasks** for actionable findings (if any):
   - Extract items from the review report and add them to `SPECS/Workplan.md`.
   - Format new or updated task entries per [`SPECS/TASK_TEMPLATE.md`](../TASK_TEMPLATE.md).
   - Assign new IDs consistent with the workflow (follow `PRIMITIVES/FOLLOW_UP.md` conventions).
   - If no actionable issues exist, explicitly note that FOLLOW-UP is skipped.

## Output

- Markdown report saved under `SPECS/INPROGRESS/REVIEW_{name}.md` or similar.
- Actionable findings with severity labels and fix suggestions.
- Test coverage assessment and explicit references to docs or PRDs.

## Integration

- Run REVIEW after `EXECUTE` but before pushing.
- Use it iteratively for large changesets; split into logical chunks if needed.
- Reference `SPECS/COMMANDS/FLOW.md` for where REVIEW fits in the pipeline.
