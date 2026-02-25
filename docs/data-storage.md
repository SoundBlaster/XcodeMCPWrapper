# Data Storage Reference

This document describes every data storage container used by mcpbridge-wrapper: the SQLite metrics database, the in-memory metrics collector, and the audit log files.

---

## Overview

mcpbridge-wrapper collects operational telemetry through three complementary layers:

| Layer | Class | Scope | Persistence |
|-------|-------|-------|-------------|
| SQLite database | `SharedMetricsStore` | Cross-process | Durable on disk |
| In-memory collector | `MetricsCollector` | Single process | Lost on exit |
| Audit log files | `AuditLogger` | Single process (loaded at startup) | Durable on disk |

All three layers are populated from the same interception point in `__main__.py` and exposed to the Web UI dashboard via `server.py`.

---

## Data Flow

```
MCP client (stdin)
       │
       ▼
  __main__.py  ─── on_request()  ──►  MetricsCollector.record_request()
       │                         ──►  SharedMetricsStore.record_request()
       │                         ──►  AuditLogger.log(direction="request")
       │
  (forward to mcpbridge)
       │
       ▼
  __main__.py  ─── on_response() ──►  MetricsCollector.record_response()
                                  ──►  SharedMetricsStore.record_response()
                                  ──►  AuditLogger.log(direction="response")

                                       ▼
                               server.py  ──  GET /api/metrics/summary
                                          ──  GET /api/metrics/timeseries
                                          ──  GET /api/audit/entries
                                          ──  GET /api/audit/export/csv
```

`__main__.py` also calls `set_client_info()` on both stores when the MCP `initialize` handshake is received (from `clientInfo.name` / `clientInfo.version` in the request params).

---

## 1. SQLite Database (`SharedMetricsStore`)

**Source file:** `src/mcpbridge_wrapper/webui/shared_metrics.py`

**Purpose:** Provides process-safe, durable storage so that all wrapper processes (e.g. multiple Zed/Cursor connections) write to the same metrics backend and the Web UI can aggregate across them.

**Default path:** `~/.cache/mcpbridge-wrapper/metrics.db`

The path can be overridden by passing a custom `db_path` to `SharedMetricsStore(db_path=...)`, which `WebUIConfig` does when the user sets a custom data directory.

**Connection model:** Each thread gets its own `sqlite3.Connection` via `threading.local()`. All writes go through a `_transaction()` context manager that commits on success and rolls back on exception. The connection timeout is 10 seconds.

---

### Table: `requests`

Stores one row per MCP tool call event. A request and its corresponding response are recorded as a single row: the request inserts the row, and the response updates it with `latency_ms` and error information.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `INTEGER` PK AUTOINCREMENT | no | Internal row identifier |
| `request_id` | `TEXT` | yes | JSON-RPC request ID (`null` for notifications) |
| `tool_name` | `TEXT` | no | MCP tool name (e.g. `XcodeGrep`) |
| `timestamp` | `REAL` | no | Unix epoch (seconds) when the request arrived |
| `latency_ms` | `REAL` | yes | End-to-end latency in milliseconds; `NULL` until the response is recorded |
| `error` | `BOOLEAN DEFAULT 0` | no | `1` if the response contained a JSON-RPC error |
| `error_code` | `INTEGER` | yes | JSON-RPC error code (e.g. `-32601`); `NULL` for successful responses |
| `error_message` | `TEXT` | yes | JSON-RPC error message string; `NULL` for successful responses |

**Indexes:**
- `idx_requests_tool` on `tool_name` — accelerates per-tool aggregation queries
- `idx_requests_time` on `timestamp` — accelerates time-window queries

**Migration note:** `error_code` and `error_message` columns were added in P12-T3 via `ALTER TABLE … ADD COLUMN` (wrapped in `contextlib.suppress` for idempotency on existing databases).

---

### Table: `client_info`

A single-row table (always `id = 1`) that records the identity of the most recently connected MCP client.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `INTEGER` PK DEFAULT 1 | no | Always `1`; enforces single-row constraint |
| `client_name` | `TEXT` | yes | Client name from `initialize` handshake (e.g. `"Cursor"`) |
| `client_version` | `TEXT` | yes | Client version string (e.g. `"1.2.3"`) |
| `updated_at` | `REAL` | yes | Unix epoch of the last update |

Rows are written with `INSERT … ON CONFLICT(id) DO UPDATE` (upsert), so there is always at most one row.

---

### Retention & Reset

- **Window:** `get_summary()` and `get_timeseries()` accept a `window_seconds` parameter (default 3 600 s = 1 hour) that filters rows by `timestamp > now - window_seconds`. Rows outside the window are still in the database but excluded from aggregation.
- **Reset:** `SharedMetricsStore.reset()` issues `DELETE FROM requests` and `DELETE FROM client_info`, removing all rows. The database file itself is not deleted.
- **No automatic purge:** Old rows are not automatically deleted; `reset()` must be called explicitly (e.g. via `POST /api/metrics/reset` in the Web UI).

---

## 2. In-Memory Collector (`MetricsCollector`)

**Source file:** `src/mcpbridge_wrapper/webui/metrics.py`

**Purpose:** Fast, lock-protected in-process accumulator for real-time dashboard metrics. Complementary to `SharedMetricsStore` — this layer provides accurate per-process latency percentiles and in-flight request counts that are difficult to compute from SQLite alone.

**Thread safety:** All mutations and reads are guarded by a single `threading.Lock`.

---

### Fields

#### Scalar counters

| Field | Type | Description |
|-------|------|-------------|
| `_total_requests` | `int` | Cumulative count of all requests since start or last reset |
| `_total_errors` | `int` | Cumulative count of all error responses |
| `_start_time` | `float` | Unix epoch when the collector was created or last reset |

#### Per-tool dictionaries

| Field | Type | Description |
|-------|------|-------------|
| `_tool_counts` | `Dict[str, int]` | Request count per tool name |
| `_tool_errors` | `Dict[str, int]` | Error count per tool name |
| `_tool_latencies` | `Dict[str, List[float]]` | All recorded latencies (ms) per tool, capped at `max_datapoints` entries |

#### Time-series deques

All deques have `maxlen=max_datapoints` (default 3 600). When full, the oldest entry is evicted automatically.

| Field | Type | Contents |
|-------|------|---------|
| `_request_times` | `Deque[float]` | Unix epoch timestamp of each request |
| `_error_times` | `Deque[float]` | Unix epoch timestamp of each error response |
| `_latency_series` | `Deque[Tuple[float, float]]` | `(timestamp, latency_ms)` pairs for all responses with known latency |

#### In-flight map

| Field | Type | Description |
|-------|------|-------------|
| `_in_flight` | `Dict[str, float]` | Maps `request_id` → start timestamp for requests that have been received but not yet responded to. Used to auto-compute `latency_ms` when `record_response()` is called without an explicit latency. Entries are removed on `record_response()`. |

#### Client identity

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `_client_name` | `str` | `"unknown"` | MCP client name from `initialize` |
| `_client_version` | `str` | `"unknown"` | MCP client version from `initialize` |

#### Error breakdown

| Field | Type | Description |
|-------|------|-------------|
| `_error_counts_by_code` | `Dict[int, int]` | Maps JSON-RPC error code → count of occurrences |

---

### Error categorisation

The module-level `categorize_error(code)` function maps a JSON-RPC error code to a severity bucket used by the dashboard for colour-coding:

| Category | Condition |
|----------|-----------|
| `"protocol"` | `-32699 ≤ code ≤ -32600` (standard JSON-RPC errors) |
| `"timeout"` | `code == -32001` |
| `"tool"` | `code ≥ 1` (Xcode-side tool execution errors) |
| `"unknown"` | Any other code, or `None` |

---

### Retention & Reset

`MetricsCollector.reset()` clears all fields:
- `_total_requests` and `_total_errors` reset to `0`
- `_start_time` set to current time
- All per-tool dicts cleared
- All deques cleared
- `_in_flight` cleared
- `_client_name` and `_client_version` reset to `"unknown"`
- `_error_counts_by_code` cleared

Data is lost on process exit — there is no persistence.

---

## 3. Audit Log Files (`AuditLogger`)

**Source file:** `src/mcpbridge_wrapper/webui/audit.py`

**Purpose:** Provides a durable, human-readable record of every MCP tool call for compliance, debugging, and post-hoc analysis. Survives process restarts.

---

### On-disk format

- **Encoding:** UTF-8 newline-delimited JSON (`.jsonl`)
- **File naming:** `audit_YYYYMMDD_HHMMSS.jsonl` (UTC timestamp)
- **Default directory:** `logs/audit/` (normalized to an absolute path at startup). Relative values resolve from the `--web-ui-config` file directory when provided, otherwise from the process working directory.
- **Rotation:** A new file is opened when the current file exceeds `max_file_size_mb` (default 10 MB). Up to `max_files` (default 10) rotated files are retained; the oldest is deleted when the limit is exceeded.
- **Startup load:** At initialisation, all `audit_*.jsonl` files in `log_dir` are read in chronological order. The most recent 10 000 entries are loaded into `_entries` in memory so the Web UI dashboard can display history from sibling processes.

---

### JSONL record fields

Each line is a JSON object. Fields are written only when non-`None`:

| Field | Type | Always present | Description |
|-------|------|---------------|-------------|
| `timestamp` | `float` | yes | Unix epoch (seconds) |
| `timestamp_iso` | `str` | yes | ISO 8601 UTC string (e.g. `"2026-02-15T10:30:00Z"`) |
| `tool` | `str` | yes | MCP tool name |
| `direction` | `str` | yes | `"request"` or `"response"` |
| `request_id` | `str` | when present | JSON-RPC request ID |
| `request` | `object` | when captured | Sanitised request payload (requires `capture_payload=True`) |
| `response` | `object` | when captured | Sanitised response payload (requires `capture_payload=True`) |
| `latency_ms` | `float` | on response | Round-trip latency in milliseconds |
| `error` | `str` | on error | Error message string |
| `error_code` | `int` | on error | JSON-RPC error code |

**Payload capture:** Disabled by default (`capture_payload=False`). When enabled, payloads larger than 64 KB are truncated to `{"_truncated": true, "raw": "<truncated JSON>"}`. The payload ring buffer holds at most 500 entries (oldest evicted).

---

### CSV export columns

`AuditLogger.export_csv()` writes a subset of fields. Extra fields in the JSONL records are silently ignored:

| Column | Description |
|--------|-------------|
| `timestamp_iso` | ISO 8601 UTC timestamp |
| `tool` | MCP tool name |
| `direction` | `"request"` or `"response"` |
| `request_id` | JSON-RPC request ID |
| `latency_ms` | Latency in milliseconds (empty for request-direction rows) |
| `error` | Error message (empty for successful responses) |

---

### Retention & Reset

- **File rotation:** Automatic at `max_file_size_mb` per file (default 10 MB), keeping `max_files` most recent (default 10). Total maximum disk usage: ~100 MB.
- **In-memory cap:** `_entries` is trimmed to the most recent 10 000 entries.
- **No reset API:** `AuditLogger` has no `reset()` method. Log files on disk persist until rotated out. The in-memory `_entries` list is repopulated from disk on restart.
- **Closing:** `AuditLogger.close()` flushes and closes the current `.jsonl` file. This is called automatically when the Web UI server shuts down.

---

## See Also

- [Architecture Overview](architecture.md) — system-level data flow diagram
- [Web UI Setup](webui-setup.md) — how to enable the dashboard
- [Environment Variables](environment-variables.md) — configuration options including custom data paths
