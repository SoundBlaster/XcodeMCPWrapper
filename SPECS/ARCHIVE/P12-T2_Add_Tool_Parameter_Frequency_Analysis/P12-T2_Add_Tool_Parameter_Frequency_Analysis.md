# PRD: P12-T2 — Add Tool Parameter Frequency Analysis

**Status:** In Progress
**Branch:** feature/P12-T2-tool-parameter-frequency-analysis
**Date:** 2026-02-16

---

## 1. Overview

Add optional capture and aggregation of tool call parameter **key names** (not values) to support pattern analysis. This enables operators to see which parameter combinations are most commonly used per tool without exposing sensitive argument values.

---

## 2. Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/webui/config.py` | Add `capture_params: bool` flag (default `False`) under the `"metrics"` key |
| `src/mcpbridge_wrapper/webui/metrics.py` | Add `record_param_keys(tool_name, param_keys)` method and `get_param_patterns(tool_name)` aggregation |
| `src/mcpbridge_wrapper/webui/shared_metrics.py` | Add `param_patterns` table; `record_param_keys()` and `get_param_patterns()` methods |
| `src/mcpbridge_wrapper/webui/server.py` | Add `GET /api/analytics/param-patterns?tool=<name>` endpoint |
| `src/mcpbridge_wrapper/__main__.py` | Extract `params.arguments` key names when `capture_params=True` and call `metrics.record_param_keys()` |
| `src/mcpbridge_wrapper/webui/static/dashboard.js` | Add expandable param pattern row in tool latency table |
| `tests/unit/webui/test_metrics.py` | New test class covering param pattern recording and retrieval |
| `tests/unit/webui/test_shared_metrics.py` | New tests for SQLite param pattern storage and `get_param_patterns` |

---

## 3. Acceptance Criteria

- [ ] `capture_params: true` in config enables parameter key capture
- [ ] Only argument key names are stored (not values) by default
- [ ] `GET /api/analytics/param-patterns?tool=XcodeGrep` returns ranked param combos
- [ ] Dashboard shows expandable param pattern info per tool in the latency table
- [ ] Default behavior (`capture_params: false`) is unchanged — no extra capture overhead
- [ ] Tests cover param extraction, aggregation, and API response format

---

## 4. Design Details

### 4.1 Config Change

Add `"capture_params": False` under the `"metrics"` section in `_DEFAULTS`. Add `capture_params` property to `WebUIConfig`.

### 4.2 Param Key Extraction

In `__main__.py` `on_request` callback: after extracting `tool_name`, if `config.capture_params` is enabled, extract `sorted(req.params.arguments.keys())` from the `MCPRequest`. The sorted tuple of key names forms a "param signature" (e.g. `("path", "pattern", "tabIdentifier")`).

### 4.3 In-Memory Metrics (MetricsCollector)

Add:
- `_param_patterns: Dict[str, Dict[Tuple[str, ...], int]]` — maps `tool_name → {signature → count}`
- `record_param_keys(tool_name: str, param_keys: List[str]) -> None` — increments counter for sorted key tuple
- `get_param_patterns(tool_name: str, top_n: int = 10) -> List[Dict[str, Any]]` — returns sorted list of `{keys: [...], count: N}` dicts

`reset()` must also clear `_param_patterns`.

### 4.4 SQLite Storage (SharedMetricsStore)

New table `param_patterns`:
```sql
CREATE TABLE IF NOT EXISTS param_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    param_signature TEXT NOT NULL,  -- JSON array of sorted key names
    count INTEGER NOT NULL DEFAULT 1,
    UNIQUE(tool_name, param_signature)
);
```

- `record_param_keys(tool_name, param_keys)`: upsert (INSERT OR REPLACE) incrementing `count`.
- `get_param_patterns(tool_name, top_n=10)`: SELECT ordered by `count DESC LIMIT top_n`.

### 4.5 API Endpoint

```
GET /api/analytics/param-patterns?tool=<name>&top_n=10
```

Response:
```json
{
  "tool": "XcodeGrep",
  "patterns": [
    {"keys": ["path", "pattern"], "count": 42},
    {"keys": ["path", "pattern", "tabIdentifier"], "count": 17}
  ]
}
```

### 4.6 Dashboard JS

In the tool latency table, add an expandable chevron button per row. On click, fetch `/api/analytics/param-patterns?tool=<toolName>` and render a sub-row listing the top param combos (formatted as `pattern, path × 42`).

---

## 5. Dependencies

- P12-T1 (MCP client identification) — ✅ completed
- `MCPRequest.params.arguments` already available in `schemas.py`
- Existing `on_request` callback in `__main__.py`

---

## 6. Non-Goals

- Do not store argument values (only key names)
- Do not add persistent storage for param patterns in the audit CSV
- Do not add a config UI for the flag; JSON config file is sufficient

---

## 7. Test Plan

### MetricsCollector
- `test_record_param_keys_basic`: record two calls with same keys → count = 2
- `test_record_param_keys_different_signatures`: two different key combos tracked separately
- `test_get_param_patterns_sorted_by_count`: returns highest-count first
- `test_get_param_patterns_top_n`: respects limit
- `test_get_param_patterns_unknown_tool`: returns empty list
- `test_reset_clears_param_patterns`

### SharedMetricsStore
- `test_record_param_keys_upserts_count`
- `test_get_param_patterns_returns_ranked_list`
- `test_get_param_patterns_unknown_tool_empty`

### Server
- `test_param_patterns_endpoint_returns_tool_patterns`
- `test_param_patterns_endpoint_unknown_tool_empty`
