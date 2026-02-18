## REVIEW REPORT — P13-T3: Multi-client transport and JSON-RPC multiplexing

**Scope:** origin/main..HEAD
**Files:** 4 changed (transport.py, daemon.py, test_broker_stubs.py, test_broker_transport.py)
**Date:** 2026-02-18

---

### Summary Verdict

- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

The implementation is sound. All acceptance criteria are met, quality gates pass (93.6% coverage), and the architecture matches the P13-T1 design spec. Two minor issues noted below; neither blocks merge.

---

### Critical Issues

None.

---

### Secondary Issues

**[Medium] Busy-wait polling loop in reconnection path may delay other client requests**

In `transport.py::_process_client_line` (lines ~265–291), when the daemon is `RECONNECTING`, the code polls with:

```python
while self._daemon.state == BrokerState.RECONNECTING:
    if time.time() > deadline:
        ...return error...
    await asyncio.sleep(0.1)
```

This is correct (non-blocking), but any request arriving during a long reconnect will hold an asyncio coroutine alive for up to `queue_ttl` seconds (default 60s). If many clients send requests simultaneously during reconnection, this creates `N × queue_ttl` worth of pending coroutines. For typical usage (few clients) this is fine. If high concurrency is expected, consider instead storing the request in a `Queue` and using a central reconnection-completion event (e.g., `asyncio.Event`) to wake all waiters simultaneously.

*Severity:* Medium — acceptable for current scale. Track as future optimization if concurrency requirements increase.

**[Low] `sessions` property returns mutable dict rather than a read-only view**

The `sessions` property documents "read-only view" but returns the underlying `_sessions` dict directly. External callers could accidentally mutate it:

```python
@property
def sessions(self) -> dict[int, ClientSession]:
    """Currently connected client sessions (read-only view)."""
    return self._sessions  # actual mutable dict
```

Fix option: `return dict(self._sessions)` or use `types.MappingProxyType`. Currently only tests use this, so risk is low.

*Severity:* Low — no current callers mutate it.

---

### Architectural Notes

1. **Direct private attribute access** — `_process_client_line` accesses `self._daemon._upstream` directly. This is intentional and documented as a tight coupling between transport and daemon layers. If the daemon interface grows, consider exposing a `write_to_upstream(line: str)` method to encapsulate this access.

2. **20-bit ID space per session** — With `_ID_MASK = 0xFFFFF`, each session can have at most ~1M simultaneous integer IDs before aliasing. JSON-RPC request IDs in practice are sequential and small, so this is not a practical concern.

3. **No `getpeereid` enforcement** — Per PRD scope, peer credential verification was deliberately deferred to a future task. This should be added before production use in multi-user environments.

4. **Notification broadcast uses raw bytes** — Notifications are forwarded using the original `line` string (not re-serialized), which is correct and efficient since no ID remapping is needed.

---

### Tests

- **32 new tests** in `test_broker_transport.py` covering all major code paths.
- **2 tests updated** in `test_broker_stubs.py` (replaced `NotImplementedError` assertions).
- Coverage: `transport.py` at **92.8%**, total project **93.6%** (≥ 90% ✅).
- Uncovered lines (7.2% in transport.py) are exception branches in `_write_to_session` write-error path and the `asyncio.start_unix_server` / `wait_closed` integration code that requires a real socket server.

---

### Next Steps

- No follow-up tasks required from this review.
- Suggested optimization (reconnect event vs busy-wait) deferred to a future improvement task if concurrency requirements increase.
- FOLLOW-UP step is **skipped** — no actionable findings warrant new backlog tasks.
