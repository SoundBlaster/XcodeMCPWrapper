# P12-T3: Add Error Classification & Categorization

**Phase:** Phase 12 — Analytics & Insights
**Priority:** P1
**Branch:** feature/P12-T3-error-classification-categorization
**Dependencies:** P10-T1 ✅

---

## Overview

Parse JSON-RPC error codes and messages from responses and categorize them into
meaningful buckets. Extend the metrics pipeline to track error breakdown, display
an error doughnut chart on the dashboard, and color-code the audit table error
column by severity.

---

## Deliverables

### 1. `src/mcpbridge_wrapper/schemas.py`
- Add `get_error_code()` and `get_error_message()` helper methods to `MCPResponse`
  that return `Optional[int]` and `Optional[str]` from `self.error.code / .message`.

### 2. `src/mcpbridge_wrapper/webui/metrics.py` (MetricsCollector)
- Add `_error_counts_by_code: Dict[int, int]` attribute.
- Extend `record_response` to accept `error_code: Optional[int] = None` and
  `error_message: Optional[str] = None` parameters.
- When `error=True` and `error_code` is provided, increment
  `_error_counts_by_code[error_code]`.
- Expose `error_counts_by_code` in `get_summary()` output.
- Reset `_error_counts_by_code` in `reset()`.

### 3. `src/mcpbridge_wrapper/webui/shared_metrics.py` (SharedMetricsStore)
- Add `error_code INTEGER` and `error_message TEXT` columns to the `requests`
  SQLite table (via `ALTER TABLE IF NOT EXISTS` pattern in `_ensure_db`).
- Extend `record_response` to accept and persist `error_code` and `error_message`.
- Extend `get_summary()` to compute and return `error_counts_by_code: Dict[int, int]`
  from the DB.

### 4. `src/mcpbridge_wrapper/__main__.py`
- In the response handler, after `_has_error(line)`, extract the error code/message
  using `MCPResponse.model_validate_json(line)` (reuse existing parse logic).
- Pass `error_code` and `error_message` to `metrics.record_response(...)`.

### 5. Error category helper (`src/mcpbridge_wrapper/webui/metrics.py`)
- Add module-level function `categorize_error(code: Optional[int]) -> str` that
  returns one of: `"protocol"` (codes -32600 to -32699), `"timeout"` (custom
  code -32001), `"tool"` (positive codes ≥ 1), `"unknown"` (everything else).

### 6. `src/mcpbridge_wrapper/webui/server.py`
- Include `error_counts_by_code` in the `/api/metrics/summary` JSON response
  (already populated from `get_summary()`; just ensure it's passed through).

### 7. `src/mcpbridge_wrapper/webui/static/index.html`
- Add a `<canvas id="error-breakdown-chart">` container in the dashboard,
  alongside the existing KPI cards (or replacing "Total Errors" card with a
  chart section beneath the KPI grid).

### 8. `src/mcpbridge_wrapper/webui/static/dashboard.js`
- Initialize a Chart.js doughnut chart (`errorBreakdownChart`) using the
  `error_counts_by_code` data from the metrics summary.
- Map codes to category labels via `categorizeError(code)`.
- Color-code audit table error column cells by severity class:
  - `error-protocol` (red) for -326xx codes
  - `error-tool` (orange) for positive codes
  - `error-timeout` (yellow) for -32001
  - `error-unknown` (grey) for all others

### 9. `src/mcpbridge_wrapper/webui/static/dashboard.css`
- Add CSS classes: `.error-protocol`, `.error-tool`, `.error-timeout`,
  `.error-unknown` with appropriate color styling.

### 10. Tests
- `tests/unit/webui/test_metrics.py`:
  - Test `categorize_error()` for all four categories.
  - Test `MetricsCollector.record_response()` with `error_code` tracks in
    `error_counts_by_code`.
  - Test `get_summary()` includes `error_counts_by_code`.
- `tests/unit/webui/test_shared_metrics.py`:
  - Test `SharedMetricsStore.record_response()` with `error_code` and `error_message`.
  - Test `get_summary()` returns `error_counts_by_code`.
- `tests/unit/test_main.py`:
  - Test that error code is extracted and passed to `metrics.record_response`.

---

## Acceptance Criteria

- [ ] JSON-RPC error code and message are extracted from error responses.
- [ ] `MetricsCollector.get_summary()` includes `error_counts_by_code`.
- [ ] `SharedMetricsStore.get_summary()` includes `error_counts_by_code`.
- [ ] Dashboard displays error breakdown doughnut chart.
- [ ] Audit table error column color-coded by severity.
- [ ] `categorize_error()` correctly maps: protocol (-326xx), timeout (-32001),
  tool (positive), unknown (rest).
- [ ] All tests pass. Coverage ≥ 90%.

---

## Dependencies

- `MCPResponse` in `schemas.py` already has `error: Optional[MCPError]` with
  `code: int` and `message: str`. No schema changes needed beyond helpers.
- Chart.js is already loaded in `index.html`.
- `_has_error()` in `__main__.py` already parses the response — reuse that parse.

---

## Out of Scope

- Storing full error payloads beyond code + message.
- Retroactive error categorization for existing audit log entries.
- WebSocket push for error breakdown (polling is sufficient).
