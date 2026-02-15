# PRD: P12-T4 — Add documentation about data storage

**Task ID:** P12-T4
**Phase:** 12 — Data Collection Enhancements
**Priority:** P2
**Status:** In Progress
**Branch:** feature/P12-T4-data-storage-documentation
**Date:** 2026-02-15

---

## 1. Problem Statement

mcpbridge-wrapper collects and persists operational telemetry across multiple storage layers: an SQLite database, in-memory structures, and structured audit log files. As new contributors or operators try to understand the system, debug issues, or extend data collection, there is no single reference explaining what data is stored where, what each field means, how data flows between components, or what happens on reset.

## 2. Goals

- Provide a comprehensive, accurate reference document for all data storage containers.
- Document every SQLite table, column, type, and nullability.
- Document the in-memory `MetricsCollector` (per-process) and `SharedMetricsStore` (cross-process) fields.
- Document the audit log format: JSONL on disk and CSV export columns.
- Explain the data flow from MCP request capture through aggregation to API exposure.
- Clarify retention and reset behaviour.
- Make the document discoverable from `docs/` (no README changes required for this scope).

## 3. Out of Scope

- No code changes — this is a pure documentation task.
- No changes to existing README.md (the docs/ folder is already referenced there).
- No ER diagram (optional stretch goal, deferred).

## 4. Deliverables

| # | Artifact | Location |
|---|----------|----------|
| 1 | Data storage reference | `docs/data-storage.md` |
| 2 | Updated module docstring | `src/mcpbridge_wrapper/webui/shared_metrics.py` — `SharedMetricsStore` class |
| 3 | Updated module docstring | `src/mcpbridge_wrapper/webui/metrics.py` — `MetricsCollector` class |

## 5. Acceptance Criteria

- [ ] SQLite schema documented with all tables (`requests`, `client_info`), columns, types, nullability, and indexes.
- [ ] In-memory `MetricsCollector` fields documented (counters, deques, dicts, in-flight map, client info, error breakdown).
- [ ] `SharedMetricsStore` documented (SQLite-backed, thread-local connections, default path, multi-process design intent).
- [ ] Audit log format documented: JSONL record fields on disk and the six CSV export columns.
- [ ] Data flow narrative: `__main__.py` capture → `metrics.py`/`shared_metrics.py` write → Web UI `server.py` API read.
- [ ] Retention/reset section covers: what `reset()` clears in each layer, default DB path, log rotation policy.
- [ ] Document lives at `docs/data-storage.md` and links back from the existing `docs/architecture.md` if appropriate.

## 6. Source Files Analysed

| File | Key classes |
|------|-------------|
| `src/mcpbridge_wrapper/webui/shared_metrics.py` | `SharedMetricsStore` — SQLite, tables: `requests`, `client_info` |
| `src/mcpbridge_wrapper/webui/metrics.py` | `MetricsCollector` — in-memory counters and deques |
| `src/mcpbridge_wrapper/webui/audit.py` | `AuditLogger` — JSONL files, CSV export |
| `src/mcpbridge_wrapper/webui/sessions.py` | Session tracking (referenced for completeness) |

## 7. Key Facts Gathered

### SQLite (`shared_metrics.db`)

**Default path:** `~/.cache/mcpbridge-wrapper/metrics.db`

**Table: `requests`**
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER PK AUTOINCREMENT | no | Row identifier |
| request_id | TEXT | yes | JSON-RPC request ID |
| tool_name | TEXT | no | MCP tool name |
| timestamp | REAL | no | Unix epoch (seconds) of request arrival |
| latency_ms | REAL | yes | Response latency; NULL until response recorded |
| error | BOOLEAN DEFAULT 0 | no | 1 if response was an error |
| error_code | INTEGER | yes | JSON-RPC error code |
| error_message | TEXT | yes | JSON-RPC error message |

Indexes: `idx_requests_tool(tool_name)`, `idx_requests_time(timestamp)`.

**Table: `client_info`**
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER PK DEFAULT 1 | no | Always 1 (single-row table) |
| client_name | TEXT | yes | MCP client name from `initialize` |
| client_version | TEXT | yes | MCP client version string |
| updated_at | REAL | yes | Unix epoch of last update |

### In-memory (`MetricsCollector`)

Counters: `_total_requests`, `_total_errors`, `_start_time`
Per-tool: `_tool_counts`, `_tool_errors`, `_tool_latencies`
Time-series deques (maxlen=3600): `_request_times`, `_error_times`, `_latency_series`
In-flight map: `_in_flight` (request_id → start timestamp)
Client info: `_client_name`, `_client_version`
Error breakdown: `_error_counts_by_code`

### Audit log (`AuditLogger`)

- On-disk format: newline-delimited JSON (`.jsonl`)
- File naming: `audit_YYYYMMDD_HHMMSS.jsonl`
- Default dir: `logs/audit/` (relative to working directory)
- Rotation: max 10 MB per file, max 10 files retained
- Memory: up to 10,000 most-recent entries loaded at startup
- CSV export columns: `timestamp_iso`, `tool`, `direction`, `request_id`, `latency_ms`, `error`

## 8. Dependencies

- P12-T1 ✅ — `client_info` table and `client_name`/`client_version` fields
- P12-T3 ✅ — `error_code`, `error_message` columns and `error_counts_by_code`

## 9. Quality Gates

This task produces only documentation files — no Python source changes.

- [ ] `ruff check src/` — must still pass (no src/ changes)
- [ ] `pytest` — must still pass (no src/ changes)
- [ ] Markdown: headings, tables, and code blocks render correctly
