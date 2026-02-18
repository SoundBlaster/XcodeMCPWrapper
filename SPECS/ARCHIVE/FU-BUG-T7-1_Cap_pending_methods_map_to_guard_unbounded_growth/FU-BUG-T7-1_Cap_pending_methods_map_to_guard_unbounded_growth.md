# PRD: FU-BUG-T7-1 — Cap `pending_methods` map to guard against unbounded growth

**Task ID:** FU-BUG-T7-1  
**Priority:** P3  
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session  
**Dependencies:** BUG-T7  
**Status:** Planned

## Objective

Prevent unbounded growth of `pending_methods` in `src/mcpbridge_wrapper/__main__.py`
while preserving BUG-T7 method-aware normalization behavior for in-flight JSON-RPC
responses.

## Deliverables

- Bounded `pending_methods` handling in `src/mcpbridge_wrapper/__main__.py`.
- Unit tests in `tests/unit/test_main.py` that verify capped growth behavior.
- Validation report at `SPECS/INPROGRESS/FU-BUG-T7-1_Validation_Report.md`.

## Acceptance Criteria

- `pending_methods` never exceeds the configured cap under sustained insert-only traffic.
- Existing request/response method correlation behavior remains unchanged.
- Regression tests for BUG-T7 behavior continue to pass.
- Full quality gates pass (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` >= 90%).

## Implementation Plan

1. Add a module-level cap constant (default `1000`) for `pending_methods`.
2. Replace raw dict updates with helper logic that evicts the oldest pending entry
   before inserting when at cap.
3. Keep response handling (`pop(request_id)`) unchanged so successful responses
   still clear pending entries.
4. Add a focused test that simulates high-volume unmatched requests and asserts the
   map size never exceeds cap.
5. Run required quality gates and write the validation report.

## Risks and Mitigations

- **Risk:** Evicting oldest entries can lose method context for delayed responses.
  **Mitigation:** Eviction only occurs once cap is reached; capped memory growth is
  the explicit priority for abnormal traffic conditions.

- **Risk:** Test could become brittle if it depends on implementation details.
  **Mitigation:** Test via observable behavior (map size and call count), not private
  container type internals.

---
**Archived:** 2026-02-18
**Verdict:** PASS
