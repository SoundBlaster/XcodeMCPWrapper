# Validation Report: FU-P13-T17 — Enable broker-hosted Web UI with shared multi-client telemetry

**Date:** 2026-02-28
**Task ID:** FU-P13-T17
**Verdict:** PASS

## Scope Implemented

- Updated `src/mcpbridge_wrapper/__main__.py` to support broker-hosted dashboard runtime:
  - `--broker-daemon --web-ui` now starts broker transport and Web UI in one process.
  - `--web-ui-only` is now rejected when combined with broker flags.
  - Added shared helpers for Web UI runtime preparation and broker spawn arg construction.
- Updated `src/mcpbridge_wrapper/broker/proxy.py`:
  - Added configurable `spawn_args` support for `--broker-spawn` flows.
  - Ensured daemon spawn command includes `--broker-daemon` plus propagated Web UI args.
- Updated `src/mcpbridge_wrapper/broker/transport.py`:
  - Added optional metrics/audit dependencies to broker transport.
  - Added broker-side client identity capture (`initialize`) and tool telemetry tracking (`tools/call` request/response latency + error state).
- Added/updated tests:
  - `tests/unit/test_main.py`
  - `tests/unit/test_broker_proxy.py`
  - `tests/unit/test_broker_transport.py`

## Quality Gates

- `PYTHONPATH=src pytest` → PASS (`689 passed, 5 skipped, 2 warnings`)
- `ruff check src/` → PASS
- `mypy src/` → PASS
- `PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` → PASS
  - Total coverage: **91.81%** (required: >= 90%)

## Acceptance Criteria Check

- [x] `mcpbridge-wrapper --broker-daemon --web-ui --web-ui-config <path>` starts broker socket and dashboard without launching direct-mode bridge loop.
- [x] `mcpbridge-wrapper --broker-spawn --web-ui --web-ui-config <path>` can auto-start a broker host with Web UI enabled.
- [x] Tool calls from multiple broker-connected clients appear in one dashboard metrics/audit stream.
- [x] Existing direct mode and broker-only behavior remain backward compatible.

## Notes

- In this environment, direct `pytest` (without `PYTHONPATH=src`) is not used for gating because imports resolve via `PYTHONPATH=src`.
