# PRD: BUG-T13 — Per-Tool Latency Statistics does not show params when `capture_params` is false

## Objective
Improve the Per-Tool Latency Statistics UX so the dashboard clearly explains why parameter data is missing when parameter capture is disabled by configuration.

## Background
When `metrics.capture_params` is `false` (default), the backend intentionally avoids parameter capture for privacy. The current UI silently omits parameter details, which looks like broken behavior instead of an intentional configuration state.

## Deliverables
- Add a visible disabled-state hint in the Per-Tool Latency Statistics table when parameter capture is disabled.
- Keep the existing detailed parameter table behavior unchanged when parameter capture is enabled.
- Add regression tests that verify the disabled-state hint behavior in served dashboard frontend code.
- Update any related docs only if implementation text needs adjustment.

## Dependencies
- Existing `/api/config` payload exposing `metrics.capture_params`.
- Existing per-tool latency table rendering logic in `src/mcpbridge_wrapper/webui/static/dashboard.js`.

## Acceptance Criteria
- [ ] When `capture_params` is `false`, the Per-Tool Latency Statistics section shows an explicit hint that parameter capture is disabled.
- [ ] The hint includes clear enablement guidance (set `metrics.capture_params: true` via web UI config).
- [ ] When `capture_params` is `true`, the hint is hidden and normal parameter details continue to render.
- [ ] Frontend regression tests cover the disabled-state hint behavior.
- [ ] Required quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Validation Plan
1. Add/extend frontend-oriented unit tests for dashboard rendering logic in `tests/unit/webui/test_server.py`.
2. Run required quality gates and capture outputs in `SPECS/INPROGRESS/BUG-T13_Validation_Report.md`.
3. Perform a brief manual read-through of generated dashboard HTML/JS responses for the disabled-state string and condition.

## Implementation Plan
### Phase 1: Frontend disabled-state messaging
- Update per-tool latency table rendering logic in `dashboard.js` to conditionally render a disabled-state row/message when parameter capture is disabled.
- Ensure the message is scoped to parameter detail content and does not affect latency/call count metrics.

### Phase 2: Backend configuration wiring verification
- Confirm dashboard config payload consumption already provides `capture_params` and wire the condition in rendering code if needed.

### Phase 3: Regression coverage and quality gates
- Add assertions in tests for disabled/enabled rendering states.
- Run quality gates and record evidence.

---
**Archived:** 2026-02-25
**Verdict:** PASS
