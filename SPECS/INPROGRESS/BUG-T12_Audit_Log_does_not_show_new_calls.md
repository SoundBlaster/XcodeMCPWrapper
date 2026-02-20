# PRD: BUG-T12 — Audit Log does not show new calls

**Task ID:** BUG-T12  
**Priority:** P1  
**Status:** In Progress  
**Owner:** Codex (flow-run)  
**Dependencies:** BUG-T8 (shared audit visibility)  

## 1. Problem Statement

The Web UI Audit Log table does not show newly recorded MCP tool calls while the dashboard is open. Users only see initial rows and cannot monitor live activity.

## 2. Scope

### In scope
- Trace backend-to-frontend update path for audit entries.
- Fix the issue so newly created audit entries are visible in the dashboard without manual page refresh.
- Add regression coverage for backend and frontend update behavior.

### Out of scope
- New audit storage backends or schema redesign.
- Dashboard visual redesign unrelated to data freshness.
- Non-audit widgets.

## 3. Deliverables

- Backend/frontend code updates required to propagate and render new audit entries.
- Tests validating new entries are emitted and displayed by update logic.
- `SPECS/INPROGRESS/BUG-T12_Validation_Report.md` with quality-gate results.

## 4. Technical Plan

1. Reproduce expected/actual behavior via existing tests and code-path inspection.
2. Inspect audit collection path:
   - `AuditLogger` write path
   - `/api/audit` response generation
   - WebSocket or polling update payloads
3. Inspect frontend audit table refresh logic and row patch/append strategy.
4. Implement minimal fix preserving existing behavior for expanded-row state and refresh cadence.
5. Add/adjust tests:
   - Backend/API test that new audit entries are returned.
   - Frontend/unit test for rendering update from new payload.
6. Run quality gates and document evidence in validation report.

## 5. Acceptance Criteria

- [ ] New tool calls appear in the Audit Log table during an active dashboard session.
- [ ] `/api/audit` returns newly created entries after calls complete.
- [ ] Existing audit row-state behavior regressions are not reintroduced.
- [ ] Targeted regression tests added/updated and passing.
- [ ] Full quality gates pass (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` with >=90% coverage).

## 6. Risks and Mitigations

- Risk: Fixing refresh logic may reintroduce row folding regressions.
  - Mitigation: Preserve ID-based incremental updates and keep existing row-state tests green.
- Risk: Backend cache or ordering changes may affect export endpoints.
  - Mitigation: Keep API schema unchanged and run integration tests around audit endpoints.

## 7. Validation Strategy

- Run focused tests for webui audit modules first.
- Run full repository quality gates.
- Capture command outputs and PASS/FAIL verdict in validation report.
