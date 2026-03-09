# Validation Report: P2-T8 — Gate broker tools/list on warmed tool catalog

**Date:** 2026-03-10
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Broker does not forward external `tools/list` while the internal tools cache is still cold | ✅ PASS |
| 2 | Empty or invalid internal `tools/list` probe results do not open the client-facing readiness gate | ✅ PASS |
| 3 | Client `tools/list` returns either a warmed catalog or a clear TTL error, never a premature empty success | ✅ PASS |
| 4 | Existing non-`tools/list` broker traffic still flows after `upstream_initialized` | ✅ PASS |
| 5 | `pytest` passes | ✅ PASS |
| 6 | `ruff check src/` passes | ✅ PASS |
| 7 | `mypy src/` passes | ✅ PASS |
| 8 | `pytest --cov` remains at or above 90% | ✅ PASS |

---

## Evidence

### Functional behavior

- Added a dedicated `tools_catalog_ready` event in the broker daemon so tool discovery
  is gated separately from the upstream `initialize` round-trip.
- The broker now treats only non-empty, structurally valid internal `tools/list`
  probe results as a ready catalog; empty or invalid results keep the gate closed,
  clear the cache, and schedule another broker-internal warm-up probe instead of
  requiring a reconnect or manual restart.
- External client `tools/list` now waits on the warmed catalog gate and returns a
  deterministic `-32001` TTL error if the broker never reaches a safe ready state.
- Non-`tools/list` methods still wait only on `upstream_initialized`, preserving the
  existing broker contract for normal request forwarding.

### Regression coverage

- `tests/unit/test_broker_daemon.py`
  - verifies catalog readiness opens only for a valid non-empty probe result
  - verifies empty probe results keep the catalog gate closed
  - verifies an empty first probe retries until a valid tool catalog becomes available
  - verifies reconnect clears both cache and readiness state
- `tests/unit/test_broker_transport.py`
  - verifies `tools/list` times out with a catalog-specific readiness error
  - verifies non-`tools/list` requests still wait on upstream initialization only
  - verifies `tools/list` resumes from the warmed cache instead of racing upstream
- `tests/integration/test_broker_multi_client.py`
  - keeps concurrent multi-client coverage aligned with the stronger broker warm-up
    contract by exercising a normal forwarded tool call path instead of the special
    cached `tools/list` path

### Validation environment hardening

- Added `pythonpath = ["src"]` to `pyproject.toml` so pytest in a clean worktree
  imports the local checkout instead of an unrelated editable install from another
  repository path. This makes FLOW validation deterministic and fixes `pytest --cov`
  reporting in multi-worktree setups.

### Command results

- `pytest` → **901 passed, 5 skipped, 2 warnings**
- `ruff check src/` → **All checks passed**
- `mypy src/` → **Success: no issues found in 20 source files**
- `pytest --cov` → **901 passed, 5 skipped, 2 warnings; coverage 91.58%**

---

## Changed Files

- `pyproject.toml`
- `src/mcpbridge_wrapper/broker/daemon.py`
- `src/mcpbridge_wrapper/broker/transport.py`
- `tests/integration/test_broker_multi_client.py`
- `tests/unit/test_broker_daemon.py`
- `tests/unit/test_broker_transport.py`
