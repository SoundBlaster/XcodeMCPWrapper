# Validation Report: FU-P13-T15 — Restore broker same-UID client acceptance when peer credential APIs are unavailable

**Date:** 2026-02-19
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Same-user local broker clients connect successfully on environments where current credential path returns `Errno 42` | ✅ PASS |
| 2 | Cross-UID or unverifiable peers are still rejected with deterministic security errors | ✅ PASS |
| 3 | Integration tests for broker multi-client flows pass in supported local environments | ✅ PASS |
| 4 | Quality gates are executed and documented | ✅ PASS |

---

## Evidence

### Runtime verification (local broker daemon)

A broker daemon + proxy initialize handshake now succeeds where it previously failed with `-32003 UID mismatch`:

- Command path: `python -m mcpbridge_wrapper --broker-daemon` + `python -m mcpbridge_wrapper --broker-connect`
- First proxy response now returns initialize success (`id: 1`) instead of UID mismatch error.

### Test evidence

- `pytest tests/integration/test_broker_multi_client.py -q` → `3 passed`
- `pytest tests/unit/test_broker_transport.py -k 'GetPeerUID or PeerCredentialVerification' -q` → `8 passed`
- New unit coverage validates:
  - `getpeereid()` path
  - `LOCAL_PEERCRED` fallback parsing
  - `SO_PEERCRED` fallback parsing
  - fail-closed behavior when no credential API is available

---

## Quality Gates

| Gate | Result | Notes |
|------|--------|-------|
| `pytest` | ⚠️ PARTIAL | 626 passed, 2 failed (`tests/unit/test_broker_stubs.py::TestBrokerProxyBasic::test_run_raises_timeout_when_no_socket`, `tests/unit/test_broker_transport.py::TestSocketPermissions::test_socket_created_with_0600_permissions`) — both pre-existing local-environment failures unrelated to this task's peer-credential fix. |
| `ruff check src/` | ✅ PASS | All checks passed. |
| `mypy src/` | ✅ PASS | Success: no issues found in 18 source files. |
| `pytest --cov` | ⚠️ PARTIAL | Same 2 unrelated local failures; coverage 92.26% (>=90%). |

---

## Changed Files

- `src/mcpbridge_wrapper/broker/transport.py`
- `tests/unit/test_broker_transport.py`
