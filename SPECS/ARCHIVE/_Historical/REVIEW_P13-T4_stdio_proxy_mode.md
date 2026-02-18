## REVIEW REPORT — P13-T4 stdio proxy mode

**Scope:** origin/main..HEAD (4 commits)
**Files:** 5 changed (proxy.py, __main__.py, test_broker_proxy.py, test_broker_stubs.py, Workplan.md)

---

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

**[Medium] `reconnect` parameter is stored but never used**
- `BrokerProxy.__init__` accepts `reconnect: bool = False` and stores `self._reconnect`, but `_run_bridge` does not implement any reconnect logic.
- The PRD §3.1 states "When reconnect is True, the proxy waits up to connect_timeout seconds for the socket to reappear (broker RECONNECTING), then reconnects." This is not implemented.
- **Fix suggestion:** Either implement the reconnect loop in `_run_bridge`, or remove the parameter and document it as a P13-T5 follow-up. Leaving dead code is misleading.

**[Low] `_make_stdout_writer` uses deprecated asyncio internals**
- `asyncio.StreamWriter(transport, protocol, None, loop)` passes `None` as the `reader` and constructs via internal constructor — this is not part of the public asyncio API and may break in future Python versions.
- **Fix suggestion:** Use `asyncio.get_event_loop().connect_write_pipe()` and hold the transport directly, or wrap stdout writes in a simple `asyncio.StreamWriter`-compatible wrapper. Consider a simpler approach that avoids `StreamWriter` altogether (write bytes directly to transport).

**[Low] `_spawn_broker_if_needed` uses `asyncio.get_event_loop()` not `asyncio.get_running_loop()`**
- `asyncio.get_event_loop()` is deprecated in Python 3.10+ when there is a running loop; `asyncio.get_running_loop()` is the correct call inside an `async` context.
- **Fix suggestion:** Replace `asyncio.get_event_loop().time()` calls with `asyncio.get_running_loop().time()` in `_spawn_broker_if_needed` and `_connect_with_timeout`.

---

### Architectural Notes

- The clean separation of `BrokerProxy.run()` from `main()` is good: the proxy lifecycle is fully testable in isolation via injected `stdin`/`stdout`.
- The `--broker-connect` / `--broker-spawn` flags use the established `_parse_*_args` pattern from `_parse_webui_args`. This is consistent with the existing codebase style.
- The `_reconnect` flag being stored-but-unused is appropriate as a forward placeholder for P13-T5, but it should be documented as such rather than silently ignored.

---

### Tests

- 15 new unit tests in `test_broker_proxy.py` — all passing.
- Stub test updated correctly to reflect that `BrokerProxy.run()` is no longer NotImplementedError.
- `_make_stdout_writer` and `_make_stdin_reader` are not unit tested (require real tty) — acceptable.
- Coverage: 90.5% total, 73.9% for `proxy.py`. Total satisfies ≥90% gate.
- No integration tests yet (deferred to P13-T5).

---

### Next Steps

1. **FU-P13-T4-1** (actionable): Fix `asyncio.get_event_loop()` → `asyncio.get_running_loop()` in `_spawn_broker_if_needed` and `_connect_with_timeout`.
2. **FU-P13-T4-2** (actionable): Implement or remove the `reconnect` parameter — document its status clearly.
3. **P13-T5** (next task): Integration tests for proxy ↔ broker session reuse and stability validation.
