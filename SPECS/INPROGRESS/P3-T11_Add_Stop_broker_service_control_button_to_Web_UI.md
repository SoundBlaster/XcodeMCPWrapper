# P3-T11 - Add Stop broker/service control button to Web UI

**Task ID:** P3-T11
**Priority:** P1
**Dependencies:** P2-T6
**Status:** Planned

## Goal

Add a dashboard control that allows users to request graceful shutdown of the running broker/service process from the Web UI when supported by the runtime mode.

## Problem Statement

The current Web UI is observability-only. Users can inspect health/metrics but cannot stop a long-running broker/service process from the dashboard. They must switch to terminal-based process management, which is slower and less discoverable.

## Deliverables

- `src/mcpbridge_wrapper/webui/server.py`
  - Add control capability endpoint (`GET /api/control`).
  - Add stop endpoint (`POST /api/control/stop`) guarded by auth.
  - Support optional shutdown callback wiring and graceful deferred trigger.
- `src/mcpbridge_wrapper/__main__.py`
  - In broker-daemon mode, wire Web UI stop callback to graceful process shutdown signaling.
- `src/mcpbridge_wrapper/webui/static/index.html`
  - Add Stop button in header controls (hidden/disabled until capability confirms support).
- `src/mcpbridge_wrapper/webui/static/dashboard.js`
  - Load control capability at startup.
  - Show/hide/label Stop button based on capability.
  - Add confirmation + stop request flow with UX state updates.
- `tests/unit/webui/test_server.py`
  - Add endpoint tests for supported/unsupported stop-control paths.
  - Verify auth still applies to control endpoints.

## Acceptance Criteria

- Dashboard exposes a Stop control only when backend reports stop capability.
- `POST /api/control/stop` returns accepted and triggers graceful broker shutdown in broker-daemon mode.
- Unsupported runtime modes return a clear non-2xx response for stop requests.
- Unit tests cover supported and unsupported stop-control behavior.
- Existing quality gates pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` (>=90%)

## Implementation Notes

- Keep control endpoints auth-protected via existing `_check_auth` path.
- Prefer deferred shutdown trigger (small async delay) so HTTP response can return before process begins teardown.
- Keep behavior explicit in API payloads (`can_stop`, `service_name`, accepted/rejected state).
- In non-broker-daemon flows, advertise no stop capability and reject stop requests with HTTP 409.

## Validation Plan

1. Add/adjust unit tests for Web UI control endpoints.
2. Run full quality gates listed above.
3. Create `SPECS/INPROGRESS/P3-T11_Validation_Report.md` with command outputs and verdict.

## Risks

- If shutdown is triggered synchronously, response delivery may race process termination.
- Non-daemon modes must not be accidentally terminated by dashboard controls.

## Out of Scope

- Start/Restart controls.
- Per-client session stop management.
- Remote process control beyond local wrapper process scope.
