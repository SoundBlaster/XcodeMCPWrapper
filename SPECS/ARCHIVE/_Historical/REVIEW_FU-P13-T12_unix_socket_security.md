## REVIEW REPORT — FU-P13-T12 unix-socket security boundary

**Scope:** origin/main..HEAD (implementation commit 8a0b812)
**Files:** 3 (1 implementation, 1 test, 1 documentation)

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None.

---

### Secondary Issues

- [Low] **`is_socket()` guard creates a minimal TOCTOU window in `start()`.**
  After `asyncio.start_unix_server()` creates the socket file and before
  `chmod(0o600)` runs, another process could open a connection (if the socket
  was created world-readable under a permissive umask).  In practice this
  window is sub-millisecond and the peer-credential check provides a second
  layer of defence, so this is a theoretical rather than practical risk.
  The `is_socket()` guard was necessary to avoid breaking existing tests that
  mock `start_unix_server` without creating a real file.

- [Low] **`SO_PEERCRED` constant hard-coded as `17` for Linux fallback.**
  `getattr(socket, "SO_PEERCRED", 17)` is the correct defensive form, but
  `17` only matches Linux (x86/ARM).  On unusual Linux ports or embedded
  targets the constant could differ.  This is acceptable for the target
  platform (macOS + standard Linux), but a comment explaining the source
  of `17` would help future maintainers (value comes from `<bits/socket.h>`).

- [Nit] **`_get_peer_uid` imports `socket` and `struct` at module level but
  they are only needed for the Linux path.** Both are stdlib, so there is no
  real overhead, but the function-level inline `import` pattern used in the
  PRD was cleaner for clarity about platform dependencies.  Not a correctness
  issue.

---

### Architectural Notes

- The two-layer defence (filesystem permissions + peer credentials) is the
  correct UNIX security model for a local-user service: the `0600` permission
  prevents other-UID `connect()` attempts at the kernel level, and the
  peer-credential check adds defence-in-depth against setuid or capability
  escalation.
- `_get_peer_uid` is a module-level function (not a method), which makes it
  cleanly patchable in tests without needing to reach into object internals.
  This follows the project's established pattern for testable helpers.
- JSON-RPC error code `-32003` is not part of the standard JSON-RPC 2.0 spec
  (which only reserves `-32700` through `-32600`). Using a non-standard code
  is acceptable here because the connection is closed immediately; the code is
  documented in the error message and in `docs/broker-mode.md`.
- `ClientSession.peer_uid` was already defined (with documentation stating
  "verified via getpeereid") — this task closed the gap between the field's
  documented intent and its actual value.

---

### Tests

- 5 new tests added to `TestPeerCredentialVerification` and `TestSocketPermissions`.
- Coverage: same-UID accept, different-UID reject, peer_uid stored on session,
  OSError fail-closed, socket `0600` permissions.
- All 553 unit tests pass; 0 regressions.
- The `TestSocketPermissions` test creates a real Unix socket, which provides
  genuine coverage of the `chmod` path.

---

### Next Steps

- [Optional] Add a code comment explaining the source of `17` for `SO_PEERCRED`.
- [Optional] Log the socket creation-to-chmod timing gap in debug output to
  make the TOCTOU window visible to operators investigating security events.
- No new follow-up tasks required — all acceptance criteria met.
