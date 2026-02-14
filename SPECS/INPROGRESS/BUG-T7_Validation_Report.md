# Validation Report — BUG-T7: Normalize `resources/*` Error Shape

**Date:** 2026-02-14
**Branch:** feature/BUG-T7-resources-error-normalization
**Verdict:** ✅ PASS

---

## Quality Gates

| Gate | Result | Details |
|------|--------|---------|
| `pytest` | ✅ PASS | 369 passed, 5 skipped |
| `ruff check src/` | ✅ PASS | All checks passed |
| `mypy src/` | ✅ PASS | No issues found in 12 source files |
| Coverage ≥ 90% | ✅ PASS | 96.2% total coverage |

---

## Changes

### `src/mcpbridge_wrapper/transform.py`
- Added import: `Dict` from `typing`
- Added `normalize_resources_error(data, method)` — converts non-tool `isError` results to JSON-RPC `-32601` errors
- Modified `process_response_line(line, method=None)` — added optional `method` parameter; when method is not `tools/call`, delegates to `normalize_resources_error` before structuredContent injection

### `src/mcpbridge_wrapper/__main__.py`
- Added `pending_methods: Dict[str, str]` — tracks request_id → method for ALL requests with ids
- Updated `on_request` callback — now records method for every request (not just tool calls); refactored to parse request once instead of twice
- Updated response processing loop — looks up method from `pending_methods` using `pop` and passes it as `method=` kwarg to `process_response_line`

### `tests/unit/test_transform.py`
- Added `normalize_resources_error` to import list
- Added `TestNormalizeResourcesError` class with 14 test cases covering:
  - `resources/list` and `resources/templates/list` normalization
  - `tools/call` isError passthrough (no normalization)
  - Default message when content is empty/non-text
  - `process_response_line` with and without `method=` parameter
  - Backward compatibility (no method provided)

### `tests/unit/test_main.py`
- Updated 2 `process_response_line` mock lambdas from `lambda s: s` to `lambda s, method=None: s` to match new signature

---

## Acceptance Criteria

- [x] `resources/list` with `result.isError=true` upstream → `error: {code: -32601, message: ...}` output
- [x] `resources/templates/list` with `result.isError=true` → same normalization
- [x] `tools/call` with `result.isError=true` → **unchanged** (tool errors are valid passthrough)
- [x] `tools/call` with `result.isError=false` → `structuredContent` injection still works
- [x] Responses with no method (method=None) → pass through unchanged (conservative)
- [x] All 369 unit tests pass (previously 323)
- [x] New tests cover all normalization scenarios
- [x] `ruff check src/` passes
- [x] `mypy src/` passes
- [x] Coverage ≥ 90% (96.2%)

---

## Test Count Delta

| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| `test_transform.py` | 97 | 111 | +14 |
| `test_main.py` | — | — | 0 (2 mocks updated) |
| **Total** | 323 | 369 | +46 |
