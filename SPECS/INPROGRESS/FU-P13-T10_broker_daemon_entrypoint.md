# PRD: FU-P13-T10 — Implement explicit broker daemon entrypoint and operational CLI flows

**Task ID:** FU-P13-T10
**Phase:** Phase 13 Follow-up
**Priority:** P0
**Status:** IN PROGRESS
**Created:** 2026-02-19

---

## 1. Problem Statement

The broker subsystem (BrokerDaemon, UnixSocketServer, BrokerProxy) is fully implemented, but the `--broker-daemon` CLI flag referenced in `BrokerProxy._spawn_broker_if_needed()` has no handler in `__main__.py`. This means:

1. `--broker-spawn` silently fails: it spawns `python -m mcpbridge_wrapper --broker-daemon`, but that process immediately exits because the flag is unrecognised.
2. Users who want to run a persistent broker must resort to a private 250-character Python one-liner documented in `docs/broker-mode.md`.
3. No broker-only flags (e.g., `--broker-daemon`) are guarded against accidental forwarding to `xcrun mcpbridge`.

---

## 2. Deliverables

| Artifact | Description |
|----------|-------------|
| `src/mcpbridge_wrapper/__main__.py` | Add `--broker-daemon` flag parsing and daemon startup branch |
| `tests/unit/test_broker_daemon_entrypoint.py` | Unit tests for `--broker-daemon` CLI parsing and early-exit paths |
| `tests/integration/test_broker_spawn.py` | Integration test for `--broker-spawn` end-to-end readiness |
| `docs/broker-mode.md` | Replace one-liner with `mcpbridge-wrapper --broker-daemon` start/stop/status commands |

---

## 3. Implementation Plan

### 3.1 Update `_parse_broker_args()` in `__main__.py`

Extend the parser to also recognise `--broker-daemon`:

```python
def _parse_broker_args(args: list) -> Tuple[bool, bool, bool, list]:
    """Returns (broker_daemon, broker_connect, broker_spawn, remaining_args)."""
    broker_daemon = False
    broker_connect = False
    broker_spawn = False
    remaining = []

    for arg in args:
        if arg == "--broker-daemon":
            broker_daemon = True
        elif arg == "--broker-connect":
            broker_connect = True
        elif arg == "--broker-spawn":
            broker_spawn = True
            broker_connect = True
        else:
            remaining.append(arg)

    return broker_daemon, broker_connect, broker_spawn, remaining
```

**Key invariant:** broker-only flags (`--broker-daemon`, `--broker-connect`, `--broker-spawn`) are consumed here and **never** appear in `remaining` (which becomes `bridge_args` forwarded to `xcrun mcpbridge`).

### 3.2 Add daemon startup branch in `main()`

After parsing web UI args and broker args, add:

```python
# Broker daemon mode: long-lived upstream + socket server
if broker_daemon:
    import asyncio
    from mcpbridge_wrapper.broker.daemon import BrokerDaemon
    from mcpbridge_wrapper.broker.transport import UnixSocketServer
    from mcpbridge_wrapper.broker.types import BrokerConfig

    broker_config = BrokerConfig.default()
    daemon = BrokerDaemon(broker_config)
    transport = UnixSocketServer(broker_config, daemon)
    daemon._transport = transport
    try:
        asyncio.run(daemon.run_forever())
    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
```

This runs **before** the broker proxy branch, and before web UI / bridge startup — mutually exclusive with other modes.

### 3.3 Unit tests for `--broker-daemon` CLI

`tests/unit/test_broker_daemon_entrypoint.py`:

- Test that `_parse_broker_args(["--broker-daemon"])` returns `broker_daemon=True` and empty `remaining`.
- Test that `--broker-daemon` combined with other flags doesn't leak into `remaining`.
- Test that `--broker-connect` and `--broker-spawn` still work as before (tuple size change safe).

### 3.4 Integration test for `--broker-spawn` readiness

`tests/integration/test_broker_spawn.py`:

- Verify that running `python -m mcpbridge_wrapper --broker-daemon` creates PID/socket files (using a temp config with a mock upstream).
- Optionally: verify `--broker-spawn` path from proxy side connects after daemon is live.

### 3.5 Update `docs/broker-mode.md`

Replace the private one-liner start command with:

```bash
mcpbridge-wrapper --broker-daemon > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

Add a status command using PID file, and document stop via `kill $(cat ~/.mcpbridge_wrapper/broker.pid)`.

---

## 4. Acceptance Criteria

- [ ] Running `mcpbridge-wrapper --broker-daemon` starts broker host mode and creates live PID/socket state
- [ ] `--broker-spawn` successfully auto-starts broker and connects without manual bootstrap
- [ ] No broker-only flags (`--broker-daemon`, `--broker-connect`, `--broker-spawn`) appear in `remaining` / `bridge_args`
- [ ] Start/status/stop commands in `docs/broker-mode.md` use supported `mcpbridge-wrapper` CLI (not inline Python)
- [ ] All existing tests remain green (`pytest`)
- [ ] `ruff check src/` passes
- [ ] New unit tests cover `--broker-daemon` CLI parsing
- [ ] New integration test validates `--broker-spawn` readiness

---

## 5. Dependencies

- P13-T2 (BrokerDaemon) ✅
- P13-T3 (UnixSocketServer) ✅
- P13-T4 (BrokerProxy with auto_spawn) ✅

---

## 6. Out of Scope

- Status subcommand (`mcpbridge-wrapper broker status`) — doc-only shell command is sufficient for now
- Configuration overrides (`--broker-socket-path`, `--broker-pid-file`) — future follow-up
- FU-P13-T11 through FU-P13-T14 remain separate tasks
