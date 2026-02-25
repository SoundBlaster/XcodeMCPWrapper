# PRD: BUG-T20 — Session Timeline can show negative duration due to incorrect entry ordering

## Objective
Eliminate negative or inverted session durations in the Session Timeline by ensuring session detection always runs on timestamp-ascending audit entries, regardless of upstream ordering.

## Background
`detect_sessions()` expects chronologically ascending entries. Some server paths currently pass newest-first arrays (or mixed ordering) into session detection, which can invert `started_at`/`ended_at` boundaries and produce impossible negative durations.

## Deliverables
- Normalize audit entry ordering before session detection in the Web UI backend session path.
- Add defensive ordering behavior at the session computation layer so callers cannot accidentally produce invalid durations.
- Add regression tests that cover newest-first and mixed-order inputs and assert non-negative durations and stable latest-event semantics.
- Document the fix and verification evidence in the validation report.

## Dependencies
- `src/mcpbridge_wrapper/webui/sessions.py`
- `src/mcpbridge_wrapper/webui/server.py`
- Existing Web UI test suites under `tests/unit/webui/` and `tests/integration/webui/`

## Acceptance Criteria
- [ ] Session detection produces non-negative duration for newest-first and mixed-order entries.
- [ ] `/api/sessions` and websocket session payloads expose monotonic session boundaries (`started_at <= ended_at`).
- [ ] Regression tests fail before the fix and pass after the fix.
- [ ] Required quality gates pass: `PYTHONPATH=src pytest`, `ruff check src/`, `mypy src/`, `PYTHONPATH=src pytest --cov` (coverage >= 90%).

## Validation Plan
1. Add/extend unit tests around session detection ordering assumptions.
2. Add/extend server-level tests to validate `/api/sessions` behavior with descending/mixed audit entries.
3. Run required quality gates and record outcomes in `SPECS/INPROGRESS/BUG-T20_Validation_Report.md`.
4. Confirm no regressions to previous BUG-T19 multi-process consistency behavior.

## Implementation Plan
### Phase 1: Defensive ordering in session detection
- Enforce timestamp-ascending ordering inside session computation to make ordering contract explicit and robust.
- Preserve output ordering expected by dashboard consumers.

### Phase 2: Server integration correctness
- Ensure all server paths that compute sessions use the normalized entry order.
- Keep payload shape unchanged.

### Phase 3: Regression coverage
- Add tests for descending/mixed input ordering and non-negative duration guarantees.
- Add server-level test asserting API session ordering and duration correctness.

---
**Planned:** 2026-02-25

---
**Archived:** 2026-02-25
**Verdict:** PASS
