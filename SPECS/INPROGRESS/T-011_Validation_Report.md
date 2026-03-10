# Validation Report: T-011 — Emit synthetic broker tools/list_changed on catalog warm-up

**Date:** 2026-03-10
**Verdict:** PASS

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Broker emits one synthetic `notifications/tools/list_changed` when a cold catalog first becomes non-empty | ✅ PASS |
| 2 | Empty retry probes do not emit synthetic notifications | ✅ PASS |
| 3 | Reconnect with an unchanged non-empty catalog remains silent | ✅ PASS |
| 4 | Reconnect with a materially changed non-empty catalog emits one new notification | ✅ PASS |
| 5 | Existing readiness gating and cached `tools/list` behavior remain intact | ✅ PASS |

---

## Evidence

### Functional behavior

- Added broker-side catalog fingerprinting so synthetic change signaling only fires on meaningful
  non-empty catalog transitions.
- Reused the existing internal warm-up probe loop rather than introducing a second watcher or
  slower polling path.
- Added transport support for a synthetic `notifications/tools/list_changed` broadcast.
- Queued that synthetic notification for sessions that have not yet completed the MCP lifecycle,
  then flushed it immediately after the client sends `notifications/initialized`.
- Preserved the current readiness gate and cached `tools/list` fast path.

### Regression coverage

- `tests/unit/test_broker_daemon.py`
  - verifies first non-empty catalog emits one synthetic notification
  - verifies empty probe results stay silent
  - verifies unchanged reconnect catalogs do not re-emit
  - verifies changed reconnect catalogs re-emit exactly once
- `tests/unit/test_broker_transport.py`
  - verifies synthetic notifications broadcast to initialized sessions
  - verifies uninitialized sessions queue the notification instead of receiving it too early
  - verifies queued notification flushes immediately after `notifications/initialized`

### Interactive broker observation

The approval harness from `T-010` was exercised against the local broker entrypoint so the
observation used the current unmerged implementation:

```bash
env PYTHONPATH=src python3 -m mcpbridge_wrapper --broker-stop

python3 scripts/xcode_approval_harness.py \
  --pretty \
  --scenario approval-probe \
  --step-delay 0.2 \
  --pause-before-step tools-list \
  --pause-seconds 30 \
  --read-timeout 10.0 \
  --final-read-timeout 20.0 \
  --output logs/xcode-approval-broker-autospawn-queued.jsonl \
  -- \
  env PYTHONPATH=src python3 -m mcpbridge_wrapper --broker
```

Observed result:

- the broker auto-spawned and completed `initialize`
- after the synchronized Xcode **Allow** click, the harness observed
  `notifications/tools/list_changed`
- the notification arrived only after the client had sent `notifications/initialized`
- the subsequent `tools/list` returned a full catalog of 20 tools
- this confirms the broker can compensate for missing upstream `list_changed` signaling on the
  approval path without regressing MCP lifecycle ordering

Summary emitted by the harness:

```json
{
  "events_recorded": 21,
  "response_ids": [1, 2, 4, 5],
  "saw_non_empty_tools_list": true,
  "saw_stdout_eof": false,
  "saw_tools_list_changed": true,
  "timeout_count": 7,
  "tools_list_sizes": [20]
}
```

Raw protocol trace:

- `logs/xcode-approval-broker-autospawn-queued.jsonl`

### Scope note

This task validates protocol-level behavior inside the broker. It does not claim that every MCP
client will always refresh UI state without reconnect; client-specific reaction to
`notifications/tools/list_changed` remains the responsibility of Cursor, Zed, or any other MCP
consumer.

---

## Quality Gate Results

| Gate | Result |
|------|--------|
| `pytest tests/unit/test_broker_daemon.py tests/unit/test_broker_transport.py -q` | 116 passed |
| `ruff check src/` | All checks passed |
| `mypy src/` | Success: no issues found in 20 source files |
| `pytest` | 920 passed, 5 skipped, 2 warnings |
| `pytest --cov` | 920 passed, 5 skipped; coverage 91.57% |

---

## Changed Files

- `src/mcpbridge_wrapper/broker/daemon.py`
- `src/mcpbridge_wrapper/broker/transport.py`
- `src/mcpbridge_wrapper/broker/types.py`
- `tests/unit/test_broker_daemon.py`
- `tests/unit/test_broker_transport.py`
