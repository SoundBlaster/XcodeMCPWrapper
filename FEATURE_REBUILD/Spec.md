# Web UI Dashboard Rebuild Specification

## Assumptions

- Source behavior is defined by branch `feature/p10-t1-web-ui` plus already integrated P10-T2 fixes.
- Rebuild scope is limited to Web UI feature architecture, reliability, and maintainability.
- Core MCP transformation behavior outside Web UI is out of scope and must remain unchanged.

## Glossary

- Web UI: Optional dashboard served by the wrapper for monitoring and audit.
- Shared Metrics Store: Process-safe metrics backend (SQLite).
- Metrics Snapshot: Current aggregated counters for dashboard KPIs.
- Timeseries Point: `{t, v}` where `t` is seconds ago and `v` is metric value.
- Audit Entry: Structured record of tool call metadata.

## Goals / Non-Goals

### Goals

- Provide a stable, explicit contract for Web UI HTTP and WebSocket interfaces.
- Preserve all current user-visible behavior unless explicitly changed in bug fixes.
- Reduce coupling between wrapper runtime and Web UI implementation details.
- Make authentication, metrics, and audit behavior deterministic and testable.

### Non-Goals

- Replace FastAPI, SQLite, or Chart.js technology choices.
- Redesign dashboard visuals or add new analytics features.
- Change default wrapper behavior when `--web-ui` is not used.

## Functional Requirements (FR)

1. FR-001: Wrapper MUST start Web UI only when `--web-ui` is present.
2. FR-002: Wrapper MUST support `--web-ui-port` and `--web-ui-config` overrides.
3. FR-003: Wrapper MUST track request lifecycle (request accepted, response matched, latency recorded).
4. FR-004: Metrics summary endpoint MUST expose stable keys used by frontend.
5. FR-005: Timeseries endpoint MUST expose arrays `requests`, `errors`, `latencies`, each of `{t, v}` points.
6. FR-006: Metrics reset endpoint MUST clear persisted and in-memory metrics state in active backend.
7. FR-007: Audit API MUST support pagination and optional tool filtering.
8. FR-008: Audit export MUST provide valid JSON and CSV payloads.
9. FR-009: Dashboard auth MUST be optional, off by default, and consistently enforced on protected endpoints.
10. FR-010: WebSocket stream MUST deliver periodic `metrics_update` payloads compatible with frontend handlers.
11. FR-011: Frontend MUST provide HTTP polling fallback when WebSocket is unavailable.
12. FR-012: Web UI dependency failures MUST return actionable startup errors.

## Non-Functional Requirements (NFR)

- NFR-001: Web UI feature overhead SHOULD remain below 1% relative to wrapper core path.
- NFR-002: Metrics and audit writes MUST be thread-safe; metrics writes MUST be process-safe.
- NFR-003: API responses SHOULD complete within 200ms in local development under normal load.
- NFR-004: Rebuild changes MUST keep test coverage for modified Web UI modules at >=90%.
- NFR-005: Defaults MUST bind dashboard to localhost (`127.0.0.1`).

## State Model & Invariants

- Request lifecycle states: `untracked -> tracked_in_flight -> completed`.
- Invariant I-001: `in_flight` count equals active tracked request IDs.
- Invariant I-002: `total_errors <= total_requests` always holds.
- Invariant I-003: Timeseries points always satisfy `0 <= t <= requested_window_seconds`.
- Invariant I-004: Audit entries are append-only and ordered by capture time.

## Persistence & Caching Rules

- Metrics persistence backend for Web UI mode MUST be shared SQLite store.
- Audit persistence MUST use rotated JSONL files with bounded retention.
- In-memory caches (audit recent entries, metrics aggregates) MAY be used for read performance but MUST not violate API contracts.

## API Contracts (Types / Inputs / Outputs / Errors)

- `GET /api/health`
  - Input: none
  - Output: `{ "status": "ok" }`
  - Errors: none expected

- `GET /api/metrics`
  - Input: none
  - Output keys (required): `uptime_seconds`, `total_requests`, `total_errors`, `rps`, `error_rate`, `tool_counts`, `tool_errors`, `tool_latency`, `in_flight`
  - Errors: auth failure `401` if auth enabled and credentials invalid/missing

- `GET /api/metrics/timeseries?seconds=<int>`
  - Input: `seconds` in `[10, 86400]`
  - Output: `{ "requests": [{"t": int, "v": number}], "errors": [...], "latencies": [...] }`
  - Errors: validation errors for invalid query, auth failures

- `POST /api/metrics/reset`
  - Input: none
  - Output: `{ "status": "ok", "message": "Metrics reset" }`
  - Errors: auth failures; storage failures

- `GET /api/audit`
  - Input: `limit`, `offset`, optional `tool`
  - Output: `{ "entries": [...], "total": int, "limit": int, "offset": int }`
  - Errors: auth failures

- `GET /api/audit/export/json`
  - Input: optional `limit`
  - Output: JSON array download
  - Errors: auth failures

- `GET /api/audit/export/csv`
  - Input: optional `limit`
  - Output: CSV download with stable header
  - Errors: auth failures

- `GET /api/config`
  - Input: none
  - Output: current config with masked password
  - Errors: auth failures

- `WS /ws/metrics`
  - Input: optional auth token flow when auth enabled
  - Output: periodic `{ "type": "metrics_update", "summary": ..., "timeseries": ... }`
  - Errors: unauthorized close when auth requirements fail

## Observability (Logs/Metrics/Events)

- Logs
  - Startup/shutdown diagnostics and dependency errors on stderr.
  - Audit log files for request/response metadata.
- Metrics
  - Total requests, total errors, RPS, error rate, in-flight count.
  - Per-tool counts and latency statistics.
- Events
  - WebSocket connection open/close.
  - Metrics reset action.
  - Audit export requests.

## Compatibility Rules (MUST / MAY)

### MUST

- MUST preserve wrapper behavior when Web UI is disabled.
- MUST preserve endpoint names and response shape expected by existing dashboard assets.
- MUST preserve process-safe metrics semantics for multi-process clients.
- MUST preserve optional authentication and default localhost binding.

### MAY

- MAY refactor internal layering and module boundaries.
- MAY improve error handling and validation messaging.
- MAY tighten contracts where behavior is currently undefined, provided docs and tests are updated in same change.

## Bug Fixes (what changes, why, and expected behavior)

- BUG-001: Keep fixed timeseries payload contract (`requests/errors/latencies` arrays of `{t,v}`), preventing empty timeline/latency charts.
- BUG-002: Align WebSocket auth handshake between server and frontend so authenticated dashboards still receive live updates.
- BUG-003: Add explicit CLI validation for invalid `--web-ui-port` values; return controlled error and non-zero exit.
- BUG-004: Align documentation and runtime behavior for Web UI environment variables to remove operator confusion.

## Acceptance Criteria (high-level)

1. Existing Web UI functionality remains intact for non-auth and auth modes.
2. Existing tests pass and added rebuild tests cover contracts and bug-fix behavior.
3. API and frontend chart contracts remain stable.
4. Multi-process metrics parity remains validated.
5. Rebuild docs (spec/architecture/workplan/harness/risks) are complete and internally consistent.
