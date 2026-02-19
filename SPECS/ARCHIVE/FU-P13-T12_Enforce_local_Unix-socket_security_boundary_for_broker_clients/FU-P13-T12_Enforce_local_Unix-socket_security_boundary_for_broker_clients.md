# PRD: FU-P13-T12 — Enforce local Unix-socket security boundary for broker clients

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Dependencies:** P13-T1 (✅), P13-T3 (✅)

---

## 1. Objective

Harden the broker's `UnixSocketServer` so that:

1. The socket file is created with `0600` permissions — no other OS users can even
   attempt a connection.
2. Each accepted connection is peer-credential-verified: if the connecting process's
   effective UID differs from the broker's own UID, the connection is rejected with
   a JSON-RPC error and closed immediately.

This closes the security gap identified in the P13-T1 ADR and aligns runtime
behaviour with the documented security model.

---

## 2. Background & Current State

### 2.1 What exists

`UnixSocketServer.start()` calls `asyncio.start_unix_server(...)` without:
- setting `0600` permissions on the created socket file.
- performing any peer-credential check on accepted connections.

`_handle_client()` already reads `peer_uid` but uses
`writer.get_extra_info("peername")` — which returns the socket *path*, not the
peer UID. So `peer_uid` is always `0` in practice, and it is never checked
against `os.getuid()`.

`ClientSession.peer_uid` (in `types.py`) is already defined and documented as
"OS-level UID of the connecting process (verified via getpeereid)" — the field
exists but the verification is missing.

### 2.2 Platform portability

| Platform | API |
|----------|-----|
| macOS    | `socket.socket.getpeereid()` — returns `(uid, gid)` |
| Linux    | `socket.getsockopt(SOL_SOCKET, SO_PEERCRED, ...)` — returns `(pid, uid, gid)` packed as three `int`s |

Both platforms are supported by `xcrun mcpbridge` targets. The implementation
must compile and test cleanly on Linux (CI) while being correct on macOS
(production).

---

## 3. Acceptance Criteria

- [ ] Broker socket file is created with `0600` permissions.
- [ ] Connections from a same-UID process are accepted normally.
- [ ] Connections from a different-UID process receive a JSON-RPC `-32003` error
      and the transport layer closes the connection without disturbing active sessions.
- [ ] `ClientSession.peer_uid` reflects the actual verified peer UID.
- [ ] Unit tests cover: same-UID accept, different-UID reject, platform fallback path.
- [ ] `docs/broker-mode.md` updated with a "Security boundary" section.
- [ ] All quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, coverage ≥ 90%.

---

## 4. Implementation Plan

### Phase A — Tests first (TDD)

Write failing tests before touching implementation code.

**File:** `tests/unit/test_broker_transport.py`

New test cases to add:

1. `TestPeerCredentialVerification`
   - `test_same_uid_client_accepted` — mock `_get_peer_uid` to return
     `os.getuid()` → client loop runs normally.
   - `test_different_uid_client_rejected` — mock to return `os.getuid() + 1` →
     client receives a `-32003` error JSON-RPC response and connection is closed.
   - `test_peer_uid_stored_on_session` — same-UID path stores correct UID on
     `ClientSession.peer_uid`.
   - `test_uid_check_failure_fallback` — mock `_get_peer_uid` to raise an
     `OSError` → connection is rejected defensively (fail-closed).

2. `TestSocketPermissions`
   - `test_socket_created_with_0600_permissions` — after `server.start()`,
     assert `stat(socket_path).st_mode & 0o777 == 0o600`.

### Phase B — Implementation

**File:** `src/mcpbridge_wrapper/broker/transport.py`

#### B-1. Add helper `_get_peer_uid(writer)`

```python
def _get_peer_uid(writer: asyncio.StreamWriter) -> int:
    """Return effective UID of the peer connected on *writer*.

    Tries macOS ``getpeereid()`` first, then Linux ``SO_PEERCRED``.
    Raises ``OSError`` if neither is available.
    """
    sock: socket.socket = writer.get_extra_info("socket")
    # macOS / BSD
    if hasattr(sock, "getpeereid"):
        uid, _gid = sock.getpeereid()
        return uid
    # Linux
    import struct
    SO_PEERCRED = 17  # socket.SO_PEERCRED not always defined
    creds = sock.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", creds)
    return uid
```

#### B-2. Enforce `0600` after `start_unix_server`

In `UnixSocketServer.start()`, after the `await asyncio.start_unix_server(...)` call:

```python
import os
socket_path_obj = Path(socket_path)
socket_path_obj.chmod(0o600)
logger.debug("Socket permissions set to 0600: %s", socket_path)
```

#### B-3. Enforce UID check in `_handle_client`

Replace the broken `peername`-based peer_uid lookup with:

```python
try:
    peer_uid = _get_peer_uid(writer)
except Exception as exc:
    logger.warning("Cannot verify peer UID on session %d: %s — rejecting.", session_id, exc)
    # Fail-closed: reject connection
    await self._send_uid_error_and_close(writer)
    return

own_uid = os.getuid()
if peer_uid != own_uid:
    logger.warning(
        "Rejected connection from UID %d (own UID %d) on session %d.",
        peer_uid, own_uid, session_id,
    )
    await self._send_uid_error_and_close(writer)
    return
```

#### B-4. Add `_send_uid_error_and_close`

```python
async def _send_uid_error_and_close(self, writer: asyncio.StreamWriter) -> None:
    """Send JSON-RPC -32003 (Forbidden) and close *writer*."""
    msg = json.dumps(
        {"jsonrpc": "2.0", "id": None,
         "error": {"code": -32003, "message": "Forbidden: UID mismatch"}},
        separators=(",", ":"),
    )
    try:
        writer.write((msg + "\n").encode())
        await writer.drain()
    except Exception:
        pass
    with contextlib.suppress(Exception):
        writer.close()
        await writer.wait_closed()
```

### Phase C — Documentation

**File:** `docs/broker-mode.md`

Add a **Security boundary** section covering:
- Socket is `0600` — only the owner can connect.
- Each connection is UID-verified; other-UID processes receive `-32003`.
- Troubleshooting hint: "Permission denied connecting to broker socket" →
  ensure client is running as the same macOS user.

---

## 5. Files Changed

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/transport.py` | Add `_get_peer_uid`, `_send_uid_error_and_close`; enforce permissions; fix `_handle_client` |
| `tests/unit/test_broker_transport.py` | New `TestPeerCredentialVerification` and `TestSocketPermissions` test classes |
| `docs/broker-mode.md` | New "Security boundary" section |

---

## 6. Notes

- Use JSON-RPC error code `-32003` (not in the standard spec but used by
  convention for "Forbidden"/"Authorization required"). Document the code in
  the error message for clarity.
- `SO_PEERCRED` constant value is `17` on Linux; prefer
  `getattr(socket, "SO_PEERCRED", 17)` for safety.
- The socket `chmod` must happen *after* `start_unix_server` because asyncio
  creates the file during that call.
- On platforms where neither `getpeereid` nor `SO_PEERCRED` is available
  (rare), the implementation must fail closed (reject the connection).
- Keep `_get_peer_uid` as a module-level function (not a method) so it is
  easily mockable in tests via `unittest.mock.patch`.
