# Validation Report: P3-T11 — Add Stop broker/service control button to Web UI

**Date:** 2026-03-01  
**Verdict:** PASS

## Summary

Implemented a Web UI stop control path for broker-daemon runtime with explicit capability discovery:
- Backend now exposes control capability and stop endpoints.
- Dashboard now renders a Stop button only when stop is supported.
- Broker-daemon mode wires stop requests to graceful self-termination signaling.

## Delivered Changes

- Added control API and stop callback plumbing:
  - `src/mcpbridge_wrapper/webui/server.py`
- Wired broker-daemon stop callback into dashboard startup:
  - `src/mcpbridge_wrapper/__main__.py`
- Added dashboard control button and action handler:
  - `src/mcpbridge_wrapper/webui/static/index.html`
  - `src/mcpbridge_wrapper/webui/static/dashboard.js`
  - `src/mcpbridge_wrapper/webui/static/dashboard.css`
- Added/updated tests for control endpoints and broker-daemon wiring:
  - `tests/unit/webui/test_server.py`
  - `tests/unit/test_main.py`

## Acceptance Criteria Check

- [x] Dashboard exposes a Stop control only when backend reports stop capability.
- [x] `POST /api/control/stop` returns accepted and triggers graceful broker shutdown in broker-daemon mode.
- [x] Unsupported runtime modes return a clear non-2xx response for stop requests.
- [x] Unit tests cover supported and unsupported stop-control behavior.
- [x] Quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Quality Gates

1. `pytest`
- Result: PASS
- Evidence: `740 passed, 5 skipped`

2. `ruff check src/`
- Result: PASS
- Evidence: `All checks passed!`

3. `mypy src/`
- Result: PASS
- Evidence: `Success: no issues found in 18 source files`

4. `pytest --cov`
- Result: PASS
- Evidence: `Required test coverage of 90.0% reached. Total coverage: 91.01%`

## Notes

- Stop capability is intentionally advertised only when `request_stop` callback is wired (broker-daemon mode).
- In unsupported modes, stop requests return HTTP 409 with actionable detail.
