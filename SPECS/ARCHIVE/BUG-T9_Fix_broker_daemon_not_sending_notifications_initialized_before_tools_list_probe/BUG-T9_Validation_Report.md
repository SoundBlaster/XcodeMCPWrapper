# BUG-T9 Validation Report

**Task:** Fix broker daemon not sending notifications/initialized before tools/list probe
**Date:** 2026-03-06
**Branch:** `fix/broker-missing-notifications-initialized`
**Verdict:** PASS

---

## Quality Gates

| Gate | Result | Detail |
|------|--------|--------|
| `pytest` | ✅ PASS | 785 passed, 5 skipped, 2 warnings |
| `ruff check src/` | ✅ PASS | All checks passed |
| `mypy src/` | ✅ PASS | No issues found in 18 source files |
| `pytest --cov` | ✅ PASS | 90.8% coverage (threshold: 90%) |

---

## Acceptance Criteria

- [x] `notifications/initialized` notification written to upstream stdin immediately after init probe ack
- [x] `notifications/initialized` appears before the `tools/list` probe in the written message sequence
- [x] `tools/list` probe response received and cached (`_tools_list_cache` populated) — confirmed via live broker trace: `TRACE: after readline raw=b'{"id":-1,...}'`
- [x] Client `initialize` → `notifications/initialized` → `tools/list` round-trip succeeds end-to-end via broker socket — confirmed: 20 tools returned
- [x] All 785 tests pass with no regressions
- [x] `ruff check src/` clean
- [x] `mypy src/` clean
- [x] Coverage ≥ 90% (actual: 90.8%)

---

## Changes Made

### `src/mcpbridge_wrapper/broker/daemon.py`

In `_read_upstream_loop`, after intercepting the init probe response (`raw_id == _BROKER_INIT_ID`),
added `notifications/initialized` notification send before the `tools/list` probe:

```python
# Complete the MCP handshake: send notifications/initialized so
# the upstream considers the session fully open before we issue
# any further requests.  Without this, xcrun mcpbridge queues
# all subsequent messages (including tools/list) indefinitely.
initialized_notif = json.dumps(
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    separators=(",", ":"),
)
upstream.stdin.write((initialized_notif + "\n").encode())
await upstream.stdin.drain()
```

### `tests/unit/test_broker_daemon.py`

Updated `test_tools_list_probe_sent_after_init_probe_acked`:
- Changed `>= 2` writes assertion to `>= 3` (init probe + notifications/initialized + tools/list)
- Added assertion that `notifications/initialized` is present in written messages
- Added ordering assertion: `notifications/initialized` index < `tools/list` index

---

## Live End-to-End Verification

Broker trace with fix applied:
```
TRACE: _upstream_initialized.SET!
TRACE: notifications/initialized sent
TRACE: before readline
TRACE: after readline raw=b'{"id":-1,"jsonrpc":"2.0","result":{"tools":[...
TRACE: before readline
```

Socket client test:
```
initialize: OK
tools/list: 20 tools - ['XcodeRefreshCodeIssuesInFile', 'BuildProject', 'XcodeWrite'] ...
```
