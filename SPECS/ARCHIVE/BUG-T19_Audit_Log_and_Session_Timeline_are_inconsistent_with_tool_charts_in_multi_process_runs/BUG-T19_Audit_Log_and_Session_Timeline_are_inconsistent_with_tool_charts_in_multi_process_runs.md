# PRD: BUG-T19 — Audit Log and Session Timeline are inconsistent with tool charts in multi-process runs

## Objective
Make Audit Log (`/api/audit`) and Session Timeline (`/api/sessions` + websocket `sessions`) use the same cross-process data source so they stay in sync with chart widgets in multi-process client setups (Cursor/Zed reconnect patterns).

## Background
Current chart/KPI widgets are backed by `SharedMetricsStore` (SQLite, process-shared), while audit/session views are currently sourced from `AuditLogger._entries` (process-local memory). Although `AuditLogger` writes JSONL logs to disk and loads startup history, it does not continuously reconcile with updates from sibling wrapper processes after startup. In multi-process workflows this creates split-brain behavior: charts update with fresh calls while audit/session views remain stale.

## Deliverables
- Implement a shared-source refresh path in `AuditLogger` so API reads can include entries written by sibling processes without requiring process restart.
- Ensure `/api/audit`, `/api/sessions`, and websocket `metrics_update.sessions` read from this same shared source path.
- Add unit/integration regression coverage that simulates multi-process logging by appending to JSONL files and verifies fresh visibility via API routes.
- Document the consistency model and any practical limits in `docs/webui-setup.md` and `docs/troubleshooting.md`.

## Dependencies
- Existing structured JSONL audit log files under configured audit log directory.
- Existing session grouping logic in `src/mcpbridge_wrapper/webui/sessions.py`.
- Existing API surface in `src/mcpbridge_wrapper/webui/server.py` and tests in `tests/unit/webui/`.

## Acceptance Criteria
- [ ] `/api/audit` includes entries written by another process after this process started (without restart).
- [ ] `/api/sessions` is computed from the same refreshed audit entry set used by `/api/audit`.
- [ ] Websocket `metrics_update` payload includes sessions built from that same refreshed source.
- [ ] Regression tests cover cross-process visibility for both audit rows and sessions.
- [ ] Documentation explains shared-source behavior and multi-process expectations.
- [ ] Required quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Validation Plan
1. Add focused tests in `tests/unit/webui/test_audit.py` for on-read history refresh behavior and stale-state recovery.
2. Extend `tests/unit/webui/test_server.py` with an API-level regression asserting `/api/audit` and `/api/sessions` observe externally appended entries from the same log directory.
3. Run full quality gates and record command outputs in `SPECS/INPROGRESS/BUG-T19_Validation_Report.md`.
4. Confirm docs updates describe consistency behavior and mention remaining independent issue tracked in `BUG-T20`.

## Implementation Plan
### Phase 1: Shared audit source reconciliation
- Add a safe refresh mechanism in `AuditLogger` that can reconcile in-memory entries with on-disk JSONL history on read paths.
- Keep ordering and memory cap behavior deterministic (`_max_memory_entries`) while avoiding malformed-line failures.
- Reuse this mechanism for `get_entries`, `get_entry_count`, and export methods so all readers observe the same source.

### Phase 2: Session path alignment with audit source
- Update server session-producing routes (`/api/sessions`, websocket loop) to consume entries from the refreshed audit source path.
- Ensure route-level behavior stays backward-compatible for query params and payload shape.
- Keep BUG-T20 scope separate: if ordering correction is needed for safety, do minimal defensive handling and avoid broad analytics changes.

### Phase 3: Regression tests and docs
- Add explicit regression tests for cross-process visibility drift.
- Update `docs/webui-setup.md` and `docs/troubleshooting.md` with consistency guarantees/limits.
- Capture all quality gate evidence in validation report.

## Notes
- Keep fix scoped to `BUG-T19` (consistency across data sources). Session-duration ordering correctness remains tracked in `BUG-T20` and should only be touched if required for safe operation of this fix.

---
**Archived:** 2026-02-25
**Verdict:** PASS
