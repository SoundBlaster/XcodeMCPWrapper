# PRD: BUG-T17 — Rows in Audit Log table automatically fold after user unfolds them

## Objective
Stabilize the Audit Log table interaction model so row expansion state persists across dashboard refresh/update cycles. Users should be able to open one or more audit rows and continue inspecting detailed payloads without the UI collapsing those rows during periodic data refreshes.

This task is scoped to the frontend rendering/update pipeline for the Audit Log widget in `src/mcpbridge_wrapper/webui/static/`. The backend API contracts (`/api/audit`, websocket update payloads) should remain unchanged unless implementation reveals an identifier stability issue that prevents reliable row-state reconciliation.

## Success Criteria
- Expanded rows remain expanded after repeated audit refreshes.
- Collapse state changes only on explicit user click.
- Behavior remains correct during active tool-call traffic.
- Existing audit rendering behavior (row ordering, detail formatting) is preserved.
- Automated tests cover the regression scenario.

## Acceptance Tests
1. Open dashboard, expand an audit row, wait through multiple refresh cycles, verify row remains expanded.
2. Expand multiple rows, confirm each remains expanded after updates.
3. Collapse one expanded row manually, verify only that row collapses.
4. Run full quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`) with coverage remaining >= 90%.

## Test-First Plan
- Identify current tests for audit dashboard rendering/update behavior.
- Add/extend a frontend unit test that reproduces auto-collapse after table update.
- Assert the fix by verifying expanded state survives multiple update invocations with stable entry identifiers.

## Execution Plan
### Phase 1: Diagnose Update Path
- Inputs: current audit table JS update functions, refresh triggers.
- Outputs: identified state reset point and reconciliation strategy.
- Verification: local code trace confirms why expansion resets.

### Phase 2: Implement State-Preserving Reconciliation
- Inputs: expansion state map keyed by stable audit entry ID.
- Outputs: incremental DOM update or rebuild path that reapplies expansion state.
- Verification: manual local behavior check under simulated repeated updates.

### Phase 3: Regression Coverage and Validation
- Inputs: frontend tests and existing web UI test suite.
- Outputs: regression test(s) proving no auto-fold.
- Verification: all quality gates pass and validation report documents evidence.

## Constraints and Decisions
- Preserve existing API schema and data polling cadence.
- Keep solution lightweight in frontend; avoid introducing new dependencies.
- Prefer deterministic keying on audit entry ID/timestamp tuple if no dedicated stable ID exists.

## Notes
- If related row-state reset patterns are discovered in adjacent widgets, capture them as follow-up tasks instead of expanding BUG-T17 scope.

---
**Archived:** 2026-02-20
**Verdict:** PASS
