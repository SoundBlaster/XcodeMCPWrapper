# FU-P13-T19 PRD — Add integration coverage for broker-hosted Web UI observability

## Objective

Add an integration test that exercises broker-mode telemetry end-to-end and validates that Web UI APIs expose aggregated metrics and audit visibility for multiple broker-connected clients. The test must simulate realistic concurrent/near-concurrent client traffic over the broker Unix socket, ensure request/response telemetry is persisted through broker transport instrumentation, and verify dashboard API consumers can read that telemetry through `/api/metrics` and `/api/audit` without race-prone assertions.

## Scope and Deliverables

- Add or update integration tests under `tests/integration/webui/`.
- Reuse real broker components (`BrokerDaemon`, `UnixSocketServer`) with a deterministic upstream test script.
- Reuse Web UI API surface (`create_app`, `TestClient`) backed by shared metrics and audit implementations used by broker-hosted mode.
- Validate success-path and error-path telemetry visibility in API responses.
- Produce execution evidence in `SPECS/INPROGRESS/FU-P13-T19_Validation_Report.md`.

## Success Criteria and Acceptance Tests

### Functional Criteria

- Aggregated metrics from broker-routed multi-client tool calls are visible via `/api/metrics`.
- At least one broker-routed error response is reflected in metrics (`total_errors`, tool error counters/error code breakdown) and audit output.
- Audit endpoint returns entries produced by broker telemetry logging (including request IDs and error fields when applicable).

### Determinism / Stability Criteria

- Assertions rely on request completion boundaries (client receives response) rather than arbitrary sleep durations.
- Any waiting for session cleanup or async propagation uses bounded polling with short timeout and clear failure messages.
- Test passes reliably in local runs and CI.

## Test-First Plan

1. Define/extend integration fixtures for:
- temporary short socket path (macOS-safe),
- deterministic upstream script that can emit both success and JSON-RPC error responses,
- broker startup/shutdown lifecycle.

2. Implement failing integration test first:
- send requests from multiple clients through broker socket,
- include one explicit failing tool call,
- query Web UI APIs and assert aggregated visibility.

3. Only adjust support code if tests expose legitimate integration gaps. If no production changes are needed, keep execution test-only.

## Execution Plan

### Phase 1: Build deterministic integration harness

- Inputs: existing broker multi-client helper patterns and Web UI e2e setup patterns.
- Outputs: broker+webui fixture(s) and request helper(s) in integration test module.
- Verification: fixture starts broker, serves API app, and tears down cleanly.

### Phase 2: Implement aggregated observability assertions

- Inputs: multi-client request streams with distinct request IDs and tool names.
- Outputs: assertions for `/api/metrics` and `/api/audit` showing combined visibility across clients.
- Verification: expected totals, tool keys, and non-empty audit entries with matching request IDs.

### Phase 3: Implement error-path observability assertions

- Inputs: one synthetic tool failure from upstream.
- Outputs: assertions for error counters/rates and audit error fields (`error`, `error_code`).
- Verification: API output includes at least one error-classified entry tied to the failing call.

## Decision Notes and Constraints

- Prefer `SharedMetricsStore` over in-memory `MetricsCollector` to mirror broker-hosted deployment behavior.
- Keep upstream behavior inside temporary script fixture to avoid monkeypatching transport internals.
- Keep assertions tolerant to naturally computed latency values (check presence/non-negative rather than exact values).

## Notes (Post-Implementation)

- If test naming or organization changes, ensure discoverability remains under `tests/integration/webui/`.
- If CI runtime increases materially, record rationale and tradeoffs in the validation report.

---
**Archived:** 2026-02-28
**Verdict:** PASS
