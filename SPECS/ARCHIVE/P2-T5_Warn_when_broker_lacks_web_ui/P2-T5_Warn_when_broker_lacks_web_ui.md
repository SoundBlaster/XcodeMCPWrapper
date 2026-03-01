# PRD: P2-T5 — Warn when --web-ui requested but running broker lacks it

## Overview

When the user starts a proxy with `--broker --web-ui` and a broker daemon is already running
without the web UI, the proxy silently connects to the existing daemon and `--web-ui` has no
effect. The user sees no web UI and no explanation. This task adds a stderr warning when the
mismatch is detected.

## Problem Statement

`_spawn_broker_if_needed` has two paths:
1. Existing broker alive → connect (skip spawn).  `--web-ui` flag was **not** passed to it at
   startup, so it has no web UI.
2. No broker → spawn a new daemon with the `spawn_args` including `--web-ui`.

In path 1, the proxy connects successfully, the MCP session works, but the web dashboard the
user expects is missing with no explanation.

## Proposed Solution

### Detection strategy

After connecting to an existing broker (path 1 above), attempt a TCP probe to
`127.0.0.1:{web_ui_port}` with a 0.5 s timeout. If the probe fails (`ConnectionRefusedError`
or `socket.timeout`), the running broker has no web UI — emit the warning.

If a new broker was just spawned (path 2), skip the probe — the daemon needs time to start its
HTTP server, and the user's intent was correctly expressed in `spawn_args`.

### Warning text

```
Warning: broker is running without --web-ui. Restart the broker to enable the dashboard.
  Hint: kill the running broker (rm ~/.mcpbridge_wrapper/broker.sock broker.pid) then reconnect.
```

The warning is printed to **stderr** so it does not corrupt the MCP JSON-RPC stream on stdout.

## Deliverables

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Add `web_ui_port` param; track `_new_broker_spawned`; add `_warn_web_ui_mismatch()` |
| `src/mcpbridge_wrapper/__main__.py` | Pass effective web UI port to `BrokerProxy` |
| `tests/unit/test_broker_proxy.py` | Add `TestBrokerProxyWebUIMismatch` (≥4 tests) |

## Implementation Plan

### 1. `proxy.py`

**`__init__`**: add `web_ui_port: int | None = None` parameter.

**Instance state**: add `self._web_ui_port = web_ui_port` and
`self._new_broker_spawned: bool = False`.

**`_spawn_broker_if_needed`**: set `self._new_broker_spawned = True` immediately before the
`subprocess.Popen` call.

**`run()`**: after successful connect (after the outer try/except block), add:
```python
if self._web_ui_port is not None and not self._new_broker_spawned:
    self._warn_web_ui_mismatch()
```

**`_warn_web_ui_mismatch()`** (synchronous helper):
```python
def _warn_web_ui_mismatch(self) -> None:
    port = self._web_ui_port
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
        # Port is accepting — web UI is present; no warning needed.
    except OSError:
        print(
            f"Warning: broker is running without --web-ui on port {port}. "
            "Restart the broker to enable the dashboard.\n"
            "  Hint: kill the running broker "
            "(rm ~/.mcpbridge_wrapper/broker.sock ~/.mcpbridge_wrapper/broker.pid) "
            "then reconnect with --broker --web-ui.",
            file=sys.stderr,
        )
```

### 2. `__main__.py`

In the `broker_connect` block, pass effective web UI port to `BrokerProxy`:

```python
_WEB_UI_DEFAULT_PORT = 8080

proxy = BrokerProxy(
    broker_config,
    auto_spawn=broker_spawn,
    connect_timeout=10.0,
    spawn_args=_build_broker_spawn_args(...),
    web_ui_port=(web_ui_port if web_ui_port is not None else _WEB_UI_DEFAULT_PORT)
    if web_ui_enabled
    else None,
)
```

### 3. `tests/unit/test_broker_proxy.py`

Add `TestBrokerProxyWebUIMismatch`:
- `test_warning_printed_when_port_refused` — web_ui_port set, existing broker, probe fails → warning in stderr
- `test_no_warning_when_port_listening` — existing broker, probe succeeds → no warning
- `test_no_warning_when_new_broker_spawned` — new spawn, port not listening → no warning (skips probe)
- `test_no_warning_when_web_ui_port_not_set` — web_ui_port=None → no warning

## Acceptance Criteria

- [ ] When `--web-ui` is passed to proxy but running broker has no web UI, a warning is printed to stderr
- [ ] Warning text is actionable (tells user how to restart the broker)
- [ ] MCP session continues normally despite the warning
- [ ] All existing tests pass
- [ ] `pytest --cov` coverage ≥ 90%
- [ ] `ruff check src/` and `ruff format --check src/ tests/` pass

## Dependencies

None.

## Risk

Low — the probe is a non-blocking TCP connect with 0.5 s timeout; it cannot hang the proxy.
The warning is stderr-only; it does not affect the JSON-RPC stream.
