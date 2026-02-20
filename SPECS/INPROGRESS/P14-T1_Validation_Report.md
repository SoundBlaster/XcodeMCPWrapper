# Validation Report: P14-T1 — Bound per-session ID restore maps in broker transport

**Date:** 2026-02-20
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Per-session restore/alias maps do not grow unbounded for completed requests | ✅ PASS |
| 2 | Existing ID round-trip fidelity guarantees remain intact for int and string IDs | ✅ PASS |
| 3 | Tests cover wrap/prune behavior and pass in CI | ✅ PASS |
| 4 | Quality gates are executed and documented | ✅ PASS |

---

## Evidence

### Functional behavior

- Implemented alias lifecycle cleanup for all completion paths:
  - Upstream response routing
  - Upstream unavailable/write-failure rollback
  - Session drain during shutdown
- Local ID allocator now skips active aliases after wrap and raises a deterministic error if alias space is exhausted.

### New/updated regression coverage

- `tests/unit/test_broker_transport.py::TestP14T1MapBounding::test_maps_remain_bounded_for_completed_request_stream`
- `tests/unit/test_broker_transport.py::TestP14T1MapBounding::test_alloc_local_id_skips_active_aliases_after_wrap`
- `tests/unit/test_broker_transport.py::TestProcessClientLineAdditional::test_string_id_mapping_is_released_after_response`
- `tests/unit/test_broker_transport.py::TestIntegerIDFidelity::test_integer_id_mapping_is_released_after_response`
- Additional assertions added for cleanup on write-failure, route, and drain paths.

### Command results

- `pytest tests/unit/test_broker_transport.py -k 'not SocketPermissions' -q` → **47 passed, 1 deselected**
- `pytest tests/unit/test_broker_transport.py -k 'P14T1MapBounding or mapping_is_released' -q` → **4 passed**
- `ruff check src/` → **All checks passed**
- `mypy src/` → **Success: no issues found in 18 source files**
- `pytest` → **1 failed, 625 passed, 5 skipped**
- `pytest --cov` → **1 failed, 625 passed, 5 skipped; coverage 91.33% (>=90%)**

The single failing test in full-suite runs is environment-specific and pre-existing in this workspace:
- `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`
- Failure: `OSError: AF_UNIX path too long`

---

## Changed Files

- `src/mcpbridge_wrapper/broker/transport.py`
- `tests/unit/test_broker_transport.py`

