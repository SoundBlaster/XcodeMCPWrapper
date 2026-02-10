# Web UI Dashboard Rebuild Architecture

## Current Pain Points (with evidence)

1. P-001: Weak abstraction between metrics implementations.
   - Evidence: `create_app()` is typed for `MetricsCollector`, but runtime passes `SharedMetricsStore` with `# type: ignore[arg-type]` in `src/mcpbridge_wrapper/__main__.py`.
   - Impact: Hidden interface drift risk and reduced static safety.

2. P-002: Shared metrics summary semantics are lossy.
   - Evidence: `SharedMetricsStore.get_summary()` computes per-tool latency percentiles with simplified approximations and derives `uptime_seconds` from the query window, not process/service lifetime in `src/mcpbridge_wrapper/webui/shared_metrics.py`.
   - Impact: Dashboard metrics can be misleading under non-trivial traffic.

3. P-003: Auth flow inconsistency for WebSocket path.
   - Evidence: server expects query token for websocket auth while dashboard websocket connection is opened without token in `src/mcpbridge_wrapper/webui/server.py` and `src/mcpbridge_wrapper/webui/static/dashboard.js`.
   - Impact: Auth-enabled deployments can lose real-time updates.

4. P-004: CLI parsing lacks resilient validation.
   - Evidence: direct `int()` casts on `--web-ui-port` values in `src/mcpbridge_wrapper/__main__.py`.
   - Impact: invalid input can terminate process with uncaught `ValueError`.

5. P-005: Operator documentation mismatch.
   - Evidence: `docs/webui-setup.md` references `MCP_WRAPPER_WEB_UI*` while code consumes `WEBUI_*` and `--web-ui`.
   - Impact: misconfiguration and support churn.

## Target Principles

- Contract-first: define shared protocols for metrics/audit/config interfaces used by server and runtime.
- Deterministic behavior: explicit validation and error boundaries at CLI/API edges.
- Compatibility-first: preserve externally visible API routes and payload schema.
- Replace type-ignore coupling with static interface compliance.
- Keep observability consistent across single-process and multi-process modes.

## Layering & Dependency Rules

- Domain Layer
  - Contains data contracts and invariants (`MetricsSummary`, `TimeseriesPoint`, `AuditEntry`).
  - No filesystem, network, or subprocess dependencies.

- Application Layer
  - Orchestrates request tracking, metrics updates, and audit recording.
  - Depends on Domain contracts and storage/transport protocols.

- Adapters Layer
  - Implements storage and transport: SQLite metrics store, in-memory metrics store, JSONL audit store, FastAPI endpoints, WebSocket stream.
  - Depends on Application and Domain.

- Interface Layer
  - CLI argument handling and entrypoint wiring.
  - Depends on Application and Adapters.

Dependency rule: higher layers must not import lower-layer concrete implementations directly; dependency inversion via protocols.

## Module Breakdown

- `webui/contracts.py`
  - Shared Protocol/TypedDict/Pydantic contracts for metrics, audit, and config snapshots.
- `webui/application/telemetry_service.py`
  - Request/response lifecycle orchestration and normalized summary/timeseries generation.
- `webui/adapters/metrics_sqlite.py`
  - Process-safe metrics persistence and query implementation.
- `webui/adapters/metrics_memory.py`
  - In-memory metrics implementation for tests and single-process tooling.
- `webui/adapters/audit_jsonl.py`
  - Rotated audit logging and exports.
- `webui/http/server.py`
  - Route definitions, auth checks, serialization.
- `__main__.py`
  - CLI parsing, bridge wiring, and service bootstrap.

## Key Data Flows (sequence bullets)

- Flow A: Startup
  - CLI parses flags -> loads config -> creates telemetry service -> starts server adapter.
- Flow B: MCP request/response tracking
  - stdin request callback -> track request id/tool/start time -> stdout response match -> record latency/error -> append audit entry.
- Flow C: Dashboard read path
  - HTTP/WS request -> auth guard -> telemetry service snapshot -> serialize stable response contract.
- Flow D: Reset path
  - POST reset -> telemetry service clear -> storage adapter reset -> acknowledgment response.

## State Management Approach

- Canonical telemetry state resides in metrics store adapter.
- Pending in-flight map remains in application layer and is bounded by active request IDs.
- Audit history uses append-only persistence plus bounded in-memory recent cache.

## Error Handling Strategy

- CLI validation errors return explicit user-facing messages and non-zero exit codes.
- Adapter failures map to bounded API errors without exposing sensitive internals.
- WebSocket auth failures return deterministic unauthorized close codes.
- Non-fatal telemetry capture failures must not break MCP forwarding path.

## Testing Strategy

- Domain/contracts: unit tests for schema stability and invariant checks.
- Application: deterministic lifecycle tests (tracked, matched, unmatched, error paths).
- Adapters: integration tests for SQLite bucketing, audit rotation, export format.
- HTTP/WS: endpoint contract tests and auth-mode tests (including websocket auth path).
- End-to-end: wrapper + web UI behavior in multi-process simulation.

## Risks

- Refactor can accidentally change payload formats if contracts are not centralized.
- Multi-process timing variability can make timeseries tests flaky if too strict.
- Auth flow changes can break existing local setups if rollout is not backward-compatible.
- Performance regressions are possible if telemetry queries become heavier without indexes.
