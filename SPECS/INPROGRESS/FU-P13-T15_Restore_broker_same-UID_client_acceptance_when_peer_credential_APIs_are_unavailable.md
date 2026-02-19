# PRD: FU-P13-T15 — Restore broker same-UID client acceptance when peer credential APIs are unavailable

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Dependencies:** FU-P13-T12 (✅), FU-P13-T14 (✅)

---

## 1. Objective

Fix broker client authentication on platforms where the current peer-UID lookup
path fails with `Errno 42 (Protocol not available)`, while preserving the local
Unix-socket security boundary introduced in FU-P13-T12.

---

## 2. Problem Summary

Current `_get_peer_uid()` behavior:
- Tries `socket.getpeereid()` when present.
- Otherwise unconditionally tries Linux `SO_PEERCRED` (defaulting constant `17`).

On the local macOS Python build used in FU-P13-T14:
- `getpeereid()` is unavailable.
- `SO_PEERCRED` is not provided by `socket` module.
- Fallback to hard-coded `17` raises `OSError: [Errno 42] Protocol not available`.

Result: broker rejects same-user local clients with `-32003 UID mismatch`.

---

## 3. Design

### 3.1 Peer UID resolution order

Refactor `_get_peer_uid()` to use platform-aware fallbacks without hard-coded
Linux constants:

1. Try `raw_sock.getpeereid()` when available.
2. Try BSD/macOS `LOCAL_PEERCRED` via `getsockopt` when available.
   - Parse returned credential bytes and extract UID.
3. Try Linux `SO_PEERCRED` only when `socket.SO_PEERCRED` exists.
4. If no supported mechanism succeeds, raise `OSError` (fail closed).

### 3.2 Security stance

- Keep fail-closed behavior for unverifiable peers.
- Keep same-UID enforcement (`peer_uid == os.getuid()`) unchanged.
- Keep `-32003` rejection path unchanged for mismatch/failure.

### 3.3 Test strategy

Add focused unit tests for `_get_peer_uid()` behavior:
- macOS/BSD path with `LOCAL_PEERCRED` payload parsing.
- Linux path only when `SO_PEERCRED` constant exists.
- Unsupported-platform path raises `OSError` (no silent allow).

Run broker transport tests plus multi-client integration to validate regression
is fixed in practical flows.

---

## 4. Files To Change

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/transport.py` | Replace hard-coded `SO_PEERCRED` fallback with platform-aware peer credential resolution |
| `tests/unit/test_broker_transport.py` | Add unit tests for LOCAL_PEERCRED/SO_PEERCRED selection and unsupported fallback handling |
| `SPECS/INPROGRESS/FU-P13-T15_Validation_Report.md` | Record quality gate and acceptance outcomes |

---

## 5. Acceptance Criteria

- [ ] Same-user local broker clients connect successfully on environments where current credential path returns `Errno 42`.
- [ ] Cross-UID or unverifiable peers are still rejected with deterministic security errors.
- [ ] Integration tests for broker multi-client flows pass in supported local environments.
- [ ] Quality gates are executed and documented.
