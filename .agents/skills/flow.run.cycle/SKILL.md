---
name: flow.run.cycle
description: Orchestrate repeated task delivery using the repository FLOW process by running one task at a time and delegating execution to $flow-run. Use when asked to process multiple tasks in sequence, run tasks in a continuous cycle, or keep shipping the next task only after the previous task pull request has passing CI.
---

# Flow Run Cycle

Run FLOW work as a strict loop with CI-gated progression.

## Contract

- Use `$flow-run` for each individual task.
- Process exactly one task cycle at a time.
- Create or switch to the next task branch only after the previous task PR has all required CI checks passing.
- Never pre-create branches for future tasks.
- If CI fails, fix issues on the same branch, push, and re-run CI review until green.

## Cycle Procedure

1. Establish cycle state.
- Inspect git status and current branch.
- Check for an existing open FLOW task branch and PR.
- If an in-flight task exists, resume from its CI state instead of starting a new branch.

2. Verify previous task CI gate.
- If there is an open PR for the previous task, run CI review (use `gh-pr-results-review`).
- Treat the gate as open only when all required checks are successful.
- If checks are pending, wait and re-check.
- If checks fail, fix failures on that same task branch and repeat CI review.

3. Start next task only after gate is open.
- Select the next task from the workplan.
- Create the new task branch only now.
- Execute the full single-task FLOW using `$flow-run` end-to-end.

4. Close the cycle iteration.
- Confirm the new PR exists for the task completed in this iteration.
- Run CI review for that PR.
- Do not move to another task until this PR is green.

5. Continue or stop.
- Continue looping only if the user asked for multiple tasks or continuous mode.
- Stop when requested, when no ready tasks remain, or when blocked by external dependencies.

## Required Behaviors

- Keep task boundaries strict: no mixed commits across tasks.
- Preserve FLOW artifact expectations under `SPECS/INPROGRESS/` and `SPECS/ARCHIVE/`.
- Report cycle status after each iteration: task ID, PR link/number, CI state, and whether next-branch creation is allowed.
- When blocked, report the blocker and exact unblock condition.

## Trigger Phrases

Use this skill when requests look like:
- "Run FLOW in a cycle for next tasks."
- "Keep doing tasks one by one, only after CI passes."
- "Automate sequential FLOW delivery with CI gating between tasks."
- "Do the next tasks continuously but never start a new branch before previous checks are green."
