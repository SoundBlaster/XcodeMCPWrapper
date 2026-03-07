# P6-T1 — Add explicit broker runtime status surface for frontend consumers

## Objective Summary

The broker already has internal lifecycle state and the Web UI already exposes
basic control metadata, but operators still have to infer real daemon health
from PID files, `--broker-status`, and raw log lines. This task adds one
explicit runtime status surface that frontend consumers can trust. The result
must make it obvious whether the dedicated broker host is healthy, reconnecting,
missing an upstream process, or serving active client sessions.

This task does not implement the TUI itself. It delivers the structured runtime
contract that a TUI or other explicit frontend can consume without log parsing.

## Deliverables

- Extend broker runtime status payloads to include operator-facing fields beyond
  the current `state` / `pid` / `upstream_pid` / `version` tuple.
- Expose that payload through the Web UI server in a dedicated API route rather
  than overloading `/api/control`.
- Cover ready, degraded, and reconnecting status states with automated tests.

## Success Criteria

- A dedicated broker host exposes structured status including broker state,
  daemon PID, upstream PID when present, version, and connected client count.
- The payload clearly distinguishes healthy vs reconnecting / not-ready states.
- Frontend consumers can detect whether upstream initialization has completed
  without reading `broker.log`.
- Existing control endpoints remain backward-compatible.

## Test-First Plan

1. Add Web UI server tests for a new broker-status endpoint and assert the JSON
   schema in both default/no-runtime and broker-runtime-backed modes.
2. Add or extend broker daemon tests for richer `status()` payloads, including
   connected session count and readiness indicators.
3. Implement the production changes only after the expected payload shape is
   fixed in tests.
4. Run full quality gates after implementation: `pytest`, `ruff check src/`,
   `mypy src/`, and `pytest --cov`.

## Execution Plan

### Phase 1: Define the runtime contract

Inputs:
- Existing `BrokerDaemon.status()` behavior
- Existing `/api/control`, `/api/config`, and `/api/sessions` routes

Outputs:
- Final status schema for frontend consumers
- Decision on how broker runtime is injected into the Web UI app

Verification:
- The schema is stable enough to power a future TUI without additional parsing
- Backward-compatible control API behavior is preserved

### Phase 2: Implement daemon + Web UI wiring

Inputs:
- `src/mcpbridge_wrapper/broker/daemon.py`
- `src/mcpbridge_wrapper/webui/server.py`
- broker-daemon startup path in `src/mcpbridge_wrapper/__main__.py`

Outputs:
- Enriched daemon status payload
- Dedicated Web UI broker-status route
- Broker daemon startup passes a runtime status provider/callback into the UI

Verification:
- A running dedicated host returns live daemon/runtime details via HTTP
- Non-broker or dashboard-only runtimes fail gracefully with a clear empty or
  unavailable status response instead of crashing

### Phase 3: Lock the behavior with tests and validation

Inputs:
- New endpoint implementation
- Existing server and broker daemon test suites

Outputs:
- Unit tests for the endpoint and status payload
- Validation report with quality gate results

Verification:
- Tests cover healthy and degraded states
- Coverage remains at or above project threshold

## Acceptance Tests

- `pytest tests/unit/test_broker_daemon.py -k status`
- `pytest tests/unit/webui/test_server.py -k broker`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- The status endpoint should report runtime data through a dedicated API route
  such as `/api/broker/status`, not by mutating `/api/control`, because control
  and observability are separate concerns.
- Session count should come from the transport/runtime object when available so
  the value reflects live attached clients rather than historical audit sessions.
- Readiness should be explicit. A frontend needs to know whether the daemon is
  merely alive or whether upstream initialization is complete.

## Notes

- If the Web UI needs a small refactor to accept an optional runtime status
  provider, keep that refactor scoped and test-covered.
- Docs updates for using this new surface belong in `P6-T3`, unless a tiny
  endpoint mention is required inline for immediate correctness.
- Review subject name for this task: `broker_runtime_status_surface`.

---
**Archived:** 2026-03-07
**Verdict:** PASS
