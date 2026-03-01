# BUG-T8 Validation Report

**Task:** BUG-T8 — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper
**Date:** 2026-03-01
**Branch:** `codex/feature/BUG-T8-fix-broker-proxy-stdout-writer`
**Verdict:** ✅ PASS

---

## Root Cause Summary

`BrokerProxy._make_stdout_writer` used `asyncio.BaseProtocol` as the protocol
for `loop.connect_write_pipe`. `asyncio.StreamWriter.drain()` calls
`protocol._drain_helper()`, which is only implemented by `FlowControlMixin`.
`BaseProtocol` does not inherit `FlowControlMixin`, so `drain()` raised
`AttributeError` on every write. `_forward_stream` caught this silently
(`except Exception: return`), causing the `socket→stdout` bridge task to exit
after the very first message (`initialize` response). `asyncio.wait(FIRST_COMPLETED)`
then cancelled the other direction, terminating the proxy.

**Impact:** All MCP clients using `--broker-spawn` or `--broker-connect` received
the `initialize` response but the proxy exited before `tools/list` could complete,
so clients showed **0 tools**.

---

## Fix Applied

**File:** `src/mcpbridge_wrapper/broker/proxy.py` — `_make_stdout_writer`

**Before:**
```python
transport, protocol = await loop.connect_write_pipe(asyncio.BaseProtocol, sys.stdout.buffer)
writer = asyncio.StreamWriter(transport, protocol, None, loop)
```

**After:**
```python
reader = asyncio.StreamReader()
protocol = asyncio.StreamReaderProtocol(reader)
transport, _ = await loop.connect_write_pipe(lambda: protocol, sys.stdout.buffer)
writer = asyncio.StreamWriter(transport, protocol, reader, loop)
```

`asyncio.StreamReaderProtocol` inherits `FlowControlMixin` and implements
`_drain_helper()`, so `drain()` works correctly and the bridge stays alive for
the full MCP session duration.

---

## Additional Fix: Pre-existing Test Isolation Bug

**File:** `tests/unit/test_broker_stubs.py` — `TestBrokerProxyBasic.setup_method`

`TestBrokerProxyBasic` used `BrokerConfig.default()` (pointing to
`~/.mcpbridge_wrapper/broker.sock`). When a live broker is running in the
developer environment, the socket exists and `_connect_with_timeout()` succeeds,
causing `test_run_raises_timeout_when_no_socket` to reach `_make_stdin_reader()`
and fail with `UnsupportedOperation` (pytest redirected stdin has no fileno).

Fixed by using a `tempfile.mkdtemp()` socket path that is guaranteed not to exist.

---

## Quality Gate Results

| Gate | Command | Result |
|------|---------|--------|
| Tests | `pytest tests/ -x -q` | ✅ 715 passed, 5 skipped |
| Lint | `ruff check src/` | ✅ All checks passed |
| Types | `mypy src/` | ✅ No issues found (18 files) |
| Coverage | `pytest --cov=src/mcpbridge_wrapper` | ✅ 91.61% (≥ 90%) |

---

## Acceptance Criteria

- [x] `_make_stdout_writer` uses `asyncio.StreamReaderProtocol` (not `asyncio.BaseProtocol`)
- [x] A proxy session forwarding `initialize` → `notifications/initialized` → `tools/list`
      returns 20 tools without the proxy exiting early (verified via manual end-to-end test)
- [x] All existing broker tests pass (`pytest tests/`)
- [x] Coverage ≥ 90%
- [x] `ruff check src/` — no lint errors
- [x] `mypy src/` — no type errors

---

## End-to-End Verification

Manual test with live broker (PID 3320, mcpbridge child approved by Xcode):

```
initialize:  OK  — serverInfo: {name: xcode-tools, version: 24582}
Proxy alive after initialize: True       ← bridge stays up (fixed)
tools/list:  ✓ 20 tools returned
  - XcodeListNavigatorIssues
  - XcodeWrite
  - DocumentationSearch
```
