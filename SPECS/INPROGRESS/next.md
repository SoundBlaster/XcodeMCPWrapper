# Next Task: BUG-T8 — Fix broker proxy bridge exits after first write due to BaseProtocol missing _drain_helper

**Status:** In progress

**Task ID:** BUG-T8
**Branch:** codex/feature/BUG-T8-fix-broker-proxy-stdout-writer
**Priority:** P0
**Selected:** 2026-03-01

## Summary

`BrokerProxy._make_stdout_writer` uses `asyncio.BaseProtocol` which does not implement `_drain_helper()`. After the first `drain()` call the bridge exits silently, causing all MCP clients in broker mode to show 0 tools after `initialize`.

## Fix

Replace `asyncio.BaseProtocol` with `asyncio.StreamReaderProtocol` (inherits `FlowControlMixin`, implements `_drain_helper`) in `_make_stdout_writer`.

## Deliverables

- `src/mcpbridge_wrapper/broker/proxy.py` patched
- Tests covering multi-message proxy session
- Validation report
