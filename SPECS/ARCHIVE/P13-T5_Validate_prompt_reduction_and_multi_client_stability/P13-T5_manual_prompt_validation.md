# Manual Prompt Validation: P13-T5

**Date:** 2026-02-19
**Task:** Validate reduced Xcode permission prompt behavior in direct mode vs broker mode
**Follow-up Task:** FU-P13-T15 (broker peer-credential fallback)

## Environment checks

- Xcode process detected: `pgrep -x Xcode` returned PID `3541`.
- Wrapper handshake command in direct mode returned MCP initialize response.
- Broker daemon socket was created at `~/.mcpbridge_wrapper/broker.sock`.

## Interactive validation procedure

1. Start from a clean broker state (remove stale pid/socket and stop old broker).
2. Run a direct-mode matrix: 1 warm-up + 5 short-lived sessions.
3. Run a broker-mode matrix against one long-lived daemon: 1 warm-up + 5 short-lived proxy sessions.
4. Capture first response line and latency per session.
5. Record observed prompt behavior and whether broker mode reaches the upstream bridge.

## Observed results

### Direct mode (`python -m mcpbridge_wrapper`)

- Warm-up + all 5 sessions returned initialize success responses.
- Typical response latency: ~0.08s to ~0.11s.
- No blocking condition observed during direct-mode runs.

### Broker mode (`python -m mcpbridge_wrapper --broker-connect`)

- Warm-up + all 5 sessions returned:
  - `{"jsonrpc":"2.0","id":null,"error":{"code":-32003,"message":"Forbidden: UID mismatch"}}`
- Broker daemon stderr consistently reported:
  - `Cannot verify peer UID ... [Errno 42] Protocol not available — rejecting connection.`
- Because proxy sessions are rejected at socket auth, broker-mode prompt behavior could not be validated.

## Result

**Status:** ❌ FAIL

- The manual prompt criterion for P13-T5 is resolved as **FAIL** due a broker-mode access regression (`-32003 UID mismatch` for same-user local connections).
- Prompt-reduction behavior cannot be confirmed while broker sessions are rejected before tool execution.
- Follow-up remediation is tracked in **FU-P13-T15**.

## Supporting evidence

- Local harness run on 2026-02-19 captured direct-mode success and broker-mode rejection across repeated short-lived sessions.
- `pytest` / `pytest --cov` failures in broker multi-client integration tests now reproduce the same `UID mismatch` behavior (`Errno 42` peer credential check path).
