# FU-P11-T2-2: Add `limit` query param to `GET /api/sessions`

**Version:** 1.0.0
**Status:** IN PROGRESS
**Priority:** P3
**Dependencies:** P11-T2 ✅
**Created:** 2026-02-16

---

## Overview

Add an optional `limit` query parameter (default: 10000, max: 10000) to the `GET /api/sessions`
endpoint that caps the number of audit entries fed to `detect_sessions()`. This prevents
slow responses when audit logs grow large.

---

## Background

`GET /api/sessions` currently hardcodes `audit.get_entries(limit=10000)`.
Callers have no way to request a shorter window of entries.
Adding `limit` as an explicit query param exposes this cap and allows clients
(e.g. the dashboard, integration tests) to request only the most-recent N entries.

---

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/webui/server.py` | Add `limit: int` Query param (default 10000, ge 1, le 10000) to `get_sessions`; pass it to `audit.get_entries()` |
| `tests/unit/webui/test_server.py` | Add tests covering default behavior, explicit limit, and boundary values |

---

## Acceptance Criteria

- [ ] `GET /api/sessions?limit=500` fetches at most 500 most-recent entries before session grouping
- [ ] Default (no `limit` param) retains current behavior — fetches up to 10,000 entries
- [ ] `limit` is validated: `ge=1`, `le=10000`
- [ ] Tests added for: default, explicit limit, min boundary (1), max boundary (10000)
- [ ] All existing tests continue to pass
- [ ] `ruff check src/` passes
- [ ] `pytest --cov` reports ≥ 90% coverage

---

## Implementation Plan

### 1. Update `server.py` — `get_sessions` endpoint

In `src/mcpbridge_wrapper/webui/server.py` at the `get_sessions` function (line ~291):

**Before:**
```python
@app.get("/api/sessions")
async def get_sessions(
    request: Request,
    gap_seconds: int = Query(default=None, ge=10, le=86400),
) -> dict[str, Any]:
    """Get tool call sessions grouped by idle gap."""
    _check_auth(request, config)
    effective_gap = gap_seconds if gap_seconds is not None else config.session_gap_seconds
    entries = audit.get_entries(limit=10000)
    sessions = detect_sessions(entries, gap_seconds=float(effective_gap))
    return {"sessions": sessions, "total": len(sessions)}
```

**After:**
```python
@app.get("/api/sessions")
async def get_sessions(
    request: Request,
    gap_seconds: int = Query(default=None, ge=10, le=86400),
    limit: int = Query(default=10000, ge=1, le=10000),
) -> dict[str, Any]:
    """Get tool call sessions grouped by idle gap."""
    _check_auth(request, config)
    effective_gap = gap_seconds if gap_seconds is not None else config.session_gap_seconds
    entries = audit.get_entries(limit=limit)
    sessions = detect_sessions(entries, gap_seconds=float(effective_gap))
    return {"sessions": sessions, "total": len(sessions)}
```

### 2. Add tests to `test_server.py`

Add a `TestGetSessionsLimit` test class that covers:
- Default limit (no `limit` param) — verifies `audit.get_entries` is called with `limit=10000`
- Explicit `limit=500` — verifies `audit.get_entries` is called with `limit=500`
- Boundary: `limit=1` — valid
- Boundary: `limit=10000` — valid
- Invalid: `limit=0` — expect 422
- Invalid: `limit=10001` — expect 422

---

## Dependencies & Risks

- No schema changes required — `limit` is a query param with a well-defined default.
- No frontend changes needed — dashboard calls without `limit` continue to work unchanged.
- No changes to `detect_sessions()` or `AuditLogger.get_entries()`.

---

## Test Plan

```
pytest tests/unit/webui/test_server.py -v
pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing
ruff check src/
```
