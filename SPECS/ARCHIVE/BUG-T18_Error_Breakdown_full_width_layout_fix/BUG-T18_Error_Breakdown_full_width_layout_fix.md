# PRD: BUG-T18 — Error Breakdown full-width layout fix

## Objective
Implement the Web UI layout change so the "Error Breakdown" widget is rendered as a full-width chart card in the dashboard, not as a half-width card inside the two-column chart grid. The fix must preserve existing responsive behavior across desktop, tablet, and mobile breakpoints and avoid regressions in dashboard rendering.

Scope is limited to frontend dashboard assets and associated regression tests:
- `src/mcpbridge_wrapper/webui/static/index.html`
- `src/mcpbridge_wrapper/webui/static/dashboard.css`
- Relevant web UI unit tests that validate served dashboard markup/contracts.

Out of scope:
- Backend metrics aggregation logic
- Chart data semantics
- Non-layout redesign of dashboard widgets

## Success Criteria
- Error Breakdown card spans the full row width in the charts layout at non-mobile breakpoints.
- Existing Tool Usage (Bar) and Tool Distribution (Pie) widgets remain correctly rendered.
- Mobile layout (`<=768px`) remains single-column and unaffected.
- Regression test coverage exists for the full-width Error Breakdown layout contract.
- All quality gates pass with coverage remaining >= 90%.

## Acceptance Tests
1. Inspect served dashboard HTML and verify Error Breakdown container uses the full-width layout class.
2. Verify CSS rules still allow full-width containers via `grid-column: 1 / -1`.
3. Manual smoke check at representative widths: `1450px`, `1200px`, `1024px`, `768px`, and narrow mobile.
4. Run quality gates:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov`

## Test-First Plan
1. Add or extend a server/web UI unit test that asserts the served dashboard markup encodes a full-width Error Breakdown container.
2. Run targeted test module to validate the new assertion fails before layout update (or verify current state is missing the contract).
3. Apply minimal markup/CSS updates to satisfy the failing test.
4. Re-run targeted tests, then full quality gates.

## Execution Plan
### Phase 1: Baseline and Contract Definition
- Inputs: current dashboard HTML/CSS and web UI tests.
- Outputs: explicit layout contract for Error Breakdown full-width behavior.
- Verification: targeted test captures required class/layout structure.

### Phase 2: Layout Implementation
- Inputs: chart row markup and existing `.chart-container.wide` CSS behavior.
- Outputs: Error Breakdown widget updated to opt into full-width spanning without changing data bindings.
- Verification: served HTML and manual viewport checks confirm full-width rendering.

### Phase 3: Regression and Validation
- Inputs: updated tests and quality gate commands.
- Outputs: passing tests, lint/type checks, and coverage report; validation report artifact.
- Verification: command outputs recorded with PASS verdict and coverage >= 90%.

## Constraints and Decisions
- Reuse existing `wide` layout contract instead of introducing a new custom layout system.
- Keep changes minimal and local to avoid unintended visual regressions.
- Preserve existing chart IDs and JS hooks to avoid runtime chart initialization breakage.

## Notes
- Update `SPECS/Workplan.md` status fields for BUG-T18 during ARCHIVE.
- If additional chart-grid responsiveness issues are discovered, track them as separate follow-up tasks rather than extending BUG-T18 scope.

---
**Archived:** 2026-02-26
**Verdict:** PASS
