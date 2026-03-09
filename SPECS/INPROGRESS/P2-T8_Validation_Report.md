# Validation Report — P2-T8

**Task:** P2-T8 — Gate broker `tools/list` on warmed tool catalog  
**Date:** 2026-03-10  
**Verdict:** PASS

## Scope

- Added a dedicated broker readiness gate for the warmed `tools/list` catalog.
- Prevented empty or invalid internal broker probes from opening the client-facing
  discovery path.
- Updated transport handling so external `tools/list` waits for the warmed cache,
  while non-`tools/list` traffic still gates only on upstream initialization.
- Added a `pytest` `pythonpath` entry so worktree-local tests resolve the checkout
  under test instead of an unrelated editable install from another clone.

## Evidence

- Broker daemon now keeps `tools_catalog_ready` separate from
  `upstream_initialized`.
- Empty broker probe results leave `_tools_list_cache` unset and keep
  `tools_catalog_ready` cleared.
- Transport returns a TTL error for cold `tools/list` requests instead of sending a
  premature empty success upstream.
- Integration coverage continues to exercise concurrent client traffic without
  relying on `tools/list` passthrough semantics.

## Required Quality Gates

- `pytest`
  - Result: **PASS** (`900 passed, 5 skipped, 2 warnings in 7.97s`)
- `ruff check src/`
  - Result: **PASS** (`All checks passed!`)
- `mypy src/`
  - Result: **PASS** (`Success: no issues found in 20 source files`)
- `pytest --cov`
  - Result: **PASS** (`900 passed, 5 skipped, 2 warnings in 8.82s`; total coverage **91.66%**, threshold 90%)

## Acceptance Criteria Status

- [x] Broker does not forward external `tools/list` while the internal tools cache is still cold.
- [x] Empty or invalid internal `tools/list` probe results do not open the client-facing readiness gate.
- [x] Client `tools/list` returns either a warmed catalog or a clear TTL error, never a premature empty success.
- [x] Existing non-`tools/list` broker traffic still flows after `upstream_initialized`.
- [x] `pytest` passes.
- [x] `ruff check src/` passes.
- [x] `mypy src/` passes.
- [x] `pytest --cov` remains at or above 90%.

## Notes

- The initial `pytest --cov` failure in this worktree was caused by an existing
  editable install pointing at `/Users/egor/Development/GitHub/XcodeMCPWrapper/src`
  instead of this worktree. Adding `pythonpath = ["src"]` makes `pytest` prefer
  the checkout-local package and restores correct coverage collection.
- Existing third-party deprecation warnings from `websockets`/`uvicorn` were
  observed during tests and are unrelated to this task.
