# PRD: FU-P12-T1-3 — Show multi-client widgets in Web UI instead of single overwritten active client

**Created:** 2026-02-18
**Priority:** P2
**Branch:** `codex/feature/FU-P12-T1-3-multi-client-widgets`
**Status:** PLAN

---

## 1. Problem Statement

The dashboard currently surfaces one `Active Client` value that is overwritten by
whichever `initialize` handshake happened most recently. This hides concurrent
or recently active clients and makes client attribution harder when multiple MCP
clients are used.

---

## 2. Scope

### In Scope
- Extend metrics summaries to include per-client aggregates (name/version,
  last seen, and initialize count).
- Keep existing `client_name`/`client_version` fields for compatibility.
- Update dashboard UI/JS to render one card per detected client.
- Add/adjust unit tests for metrics, shared metrics, and server API behavior.

### Out of Scope
- Historical backfill from old logs.
- Authentication or transport changes.
- Session timeline redesign.

---

## 3. Deliverables

1. Backend metrics data model
- `src/mcpbridge_wrapper/webui/metrics.py`
- `src/mcpbridge_wrapper/webui/shared_metrics.py`
- Summary payload includes `clients` array for dashboard consumption.

2. Web UI rendering updates
- `src/mcpbridge_wrapper/webui/static/index.html`
- `src/mcpbridge_wrapper/webui/static/dashboard.js`
- `src/mcpbridge_wrapper/webui/static/dashboard.css`

3. Test coverage
- `tests/unit/webui/test_metrics.py`
- `tests/unit/webui/test_shared_metrics.py`
- `tests/unit/webui/test_server.py`

4. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T1-3_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] Dashboard shows multiple clients simultaneously when more than one client connects.
- [ ] Existing single-client behavior remains correct when only one client is present.
- [ ] Client widgets update in real time with the same refresh cadence as other KPIs.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- P12-T1 ✅

---

## 6. Risks and Mitigations

- **Risk:** Shared SQLite schema migration could break older DB files.
  - **Mitigation:** Use additive table creation (`CREATE TABLE IF NOT EXISTS`) and
    non-destructive upserts.
- **Risk:** UI changes regress KPI rendering.
  - **Mitigation:** Keep existing KPI IDs used by JS and add focused rendering
    helpers for new client cards.

---

## 7. Validation Plan

1. Add `clients` summary support in in-memory and shared metrics collectors.
2. Render per-client cards in dashboard from `summary.clients`.
3. Add tests for multi-client summary/API behavior.
4. Run required quality gates and document results.

---
