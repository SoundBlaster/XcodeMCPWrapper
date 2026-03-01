# BUG-T8: Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper

**Task ID:** BUG-T8
**Branch:** `codex/feature/BUG-T8-fix-broker-proxy-stdout-writer`
**Priority:** P0
**Created:** 2026-03-01
**Status:** In progress

---

## Problem Statement

`BrokerProxy._make_stdout_writer` (in `src/mcpbridge_wrapper/broker/proxy.py`) wraps
`sys.stdout.buffer` using `asyncio.BaseProtocol` as the protocol factory:

```python
transport, protocol = await loop.connect_write_pipe(asyncio.BaseProtocol, sys.stdout.buffer)
writer = asyncio.StreamWriter(transport, protocol, None, loop)
```

`asyncio.StreamWriter.drain()` calls `self._protocol._drain_helper()`, which is implemented
by `asyncio.streams.FlowControlMixin`. `asyncio.BaseProtocol` does **not** inherit
`FlowControlMixin` and therefore does **not** have `_drain_helper`.

### Failure Sequence

1. Proxy receives `initialize` request from MCP client (e.g. Zed with `--broker-spawn`).
2. Proxy forwards to broker socket, gets response.
3. `_forward_stream(sock_reader, stdout_writer)` writes the response line via `writer.write(line)`.
4. `await writer.drain()` calls `protocol._drain_helper()` → `AttributeError` raised.
5. `except Exception as exc: return` in `_forward_stream` silently swallows the error and returns.
6. `asyncio.wait(FIRST_COMPLETED)` sees `sock→stdout` task done, cancels `stdin→sock`.
7. Proxy process exits.
8. MCP client receives `initialize` response but the proxy is gone before `tools/list` can complete.
9. Client shows **0 tools**.

### Impact

All MCP clients using `--broker-spawn` or `--broker-connect` are affected:
- Zed IDE shows "0 tools"
- Any other stdio-based broker proxy session terminates after one response

---

## Root Cause

Wrong protocol class in `_make_stdout_writer`. Should use `asyncio.StreamReaderProtocol`
(which inherits `FlowControlMixin`) instead of `asyncio.BaseProtocol`.

---

## Fix

Replace `asyncio.BaseProtocol` with the standard asyncio streams pattern:

```python
@staticmethod
async def _make_stdout_writer() -> asyncio.StreamWriter:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    transport, _ = await loop.connect_write_pipe(lambda: protocol, sys.stdout.buffer)
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    return writer
```

`asyncio.StreamReaderProtocol` inherits `FlowControlMixin`, which implements
`_drain_helper()`, so `drain()` works correctly and the bridge stays alive for
the full MCP session.

---

## Deliverables

1. **`src/mcpbridge_wrapper/broker/proxy.py`** — `_make_stdout_writer` patched (already applied).
2. **Tests** — existing proxy tests must pass; add/update test(s) that exercise a multi-message
   proxy session (initialize → notifications/initialized → tools/list) to prevent regression.
3. **`SPECS/INPROGRESS/BUG-T8_Validation_Report.md`** — quality gate results.

---

## Acceptance Criteria

- [ ] `_make_stdout_writer` uses `asyncio.StreamReaderProtocol` (not `asyncio.BaseProtocol`)
- [ ] A proxy session forwarding `initialize` → `notifications/initialized` → `tools/list`
      returns responses for all three messages without the proxy exiting early
- [ ] All existing broker tests pass (`pytest tests/`)
- [ ] Coverage ≥ 90% (`pytest --cov`)
- [ ] `ruff check src/` — no lint errors
- [ ] `mypy src/` — no type errors

---

## Dependencies

None.

---

## Test Plan

1. Run full test suite: `pytest tests/ -x`
2. Run coverage: `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`
3. Run lint: `ruff check src/`
4. Run type check: `mypy src/`
5. Verify end-to-end via raw socket test: broker running → `initialize` + `tools/list` → 20 tools
