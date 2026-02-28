# FU-P11-T2-3: Reorder sessions from the last to the first

**Version:** 1.0.0
**Status:** IN PROGRESS
**Priority:** P2
**Dependencies:** P11-T2 ✅
**Created:** 2026-02-28

---

## Overview

Make the Session Timeline newest-first by returning sessions in descending start-time order.
This ensures the latest activity appears at the top and is labeled as `Session 1`.

---

## Background

The backend session detector currently returns sessions chronologically (oldest-to-newest).
`renderTimeline()` uses the returned array order for labels, so the oldest session is rendered as
`Session 1`. This makes fresh activity harder to find during active debugging.

---

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/webui/sessions.py` | Return sessions newest-first while preserving deterministic session IDs and tool ordering inside each session |
| `tests/unit/webui/test_sessions.py` | Update ordering expectations and add explicit newest-first assertions |
| `tests/unit/webui/test_server.py` | Add/adjust API/WebSocket assertions to verify newest-first session ordering |

---

## Acceptance Criteria

- [ ] `GET /api/sessions` returns sessions ordered by latest start time first
- [ ] Timeline labels show the newest group as `Session 1`
- [ ] Refresh and live updates keep the same newest-first ordering
- [ ] Tests cover ordering with at least two sessions at different timestamps
- [ ] `pytest` passes
- [ ] `ruff check src/` passes
- [ ] `mypy src/` passes
- [ ] `pytest --cov` reports ≥ 90% coverage

---

## Implementation Plan

### 1. Update session ordering at source (`sessions.py`)

- Build sessions in chronological order as today (to keep gap grouping logic simple).
- Reverse the completed session list before returning.
- Reindex session IDs after reversal so `session_0` maps to newest session and labels remain intuitive.
- Keep each session's `tools` list in chronological order to preserve intra-session call flow.

### 2. Validate API and WebSocket behavior (`test_server.py`)

- Add endpoint-level assertion that multi-session responses are newest-first.
- Add WebSocket assertion that pushed `sessions` payload is newest-first.

### 3. Validate detector behavior (`test_sessions.py`)

- Update existing multi-session tests to assert newest-first ordering.
- Add explicit test ensuring `session_0` corresponds to newest session.

---

## Risks and Mitigations

- **Risk:** Existing tests or UI logic rely on oldest-first order.
  - **Mitigation:** Update tests and keep tool ordering within a session unchanged.

- **Risk:** Session IDs could become unstable after reordering.
  - **Mitigation:** Reindex IDs after final ordering so IDs are deterministic and label-safe.

---

## Test Plan

```bash
pytest
ruff check src/
mypy src/
pytest --cov
```

---
**Archived:** 2026-02-28
**Verdict:** PASS
