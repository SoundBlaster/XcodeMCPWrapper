# PRD: BUG-T14 — Rows in Per-Tool Latency Statistics fold automatically immediately after unfolding

## Objective
Keep Per-Tool Latency table expansion state stable across periodic metrics refreshes so expanded parameter rows remain open until the user explicitly collapses them.

This task is scoped to the frontend dashboard logic in `src/mcpbridge_wrapper/webui/static/dashboard.js` and related Web UI regression tests. Backend APIs and metrics payload schemas should remain unchanged.

## Success Criteria
- Expanded Per-Tool Latency rows remain expanded across repeated dashboard refresh cycles.
- Row collapse only occurs on explicit user action.
- Existing latency metrics rendering and sorting behavior are preserved.
- Regression coverage is added for state-preservation logic.

## Acceptance Tests
1. Open dashboard and expand one tool row in Per-Tool Latency table.
2. Wait through multiple refresh cycles and verify row stays expanded.
3. Expand multiple tool rows and verify each remains expanded.
4. Collapse one row and verify it remains collapsed on subsequent refresh.
5. Run full quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`) with coverage >= 90%.

## Test-First Plan
- Extend static asset regression assertions in `tests/unit/webui/test_server.py` to require latency table expansion-state preservation hooks.
- Implement frontend state tracking keyed by tool name and verify tests pass.

## Execution Plan
### Phase 1: Diagnose and Design
- Confirm where `updateLatencyTable` rebuilds DOM and drops expansion state.
- Define stable keying strategy for expanded rows (`tool` string).

### Phase 2: Implement State Preservation
- Add persistent expansion-state map for latency table rows.
- Capture currently-expanded rows before table re-render and reapply after rebuild.
- Ensure click toggle updates state map consistently.

### Phase 3: Validate and Document
- Add/update regression tests for dashboard.js static behavior expectations.
- Run full quality gates and record outcomes in validation report.

## Constraints and Decisions
- No new dependencies; keep implementation in vanilla frontend JS.
- Preserve existing parameter-pattern fetch API behavior.
- Avoid backend contract changes for this bugfix.

## Notes
- If this work reveals broader full-re-render UX regressions in related widgets, capture them as separate follow-up tasks.

---
**Archived:** 2026-02-20
**Verdict:** PASS
