# PRD: P13-T4 — Add stdio proxy mode for compatibility with existing MCP clients

**Status:** IN PROGRESS
**Priority:** P1
**Branch:** `feature/P13-T4-stdio-proxy-mode`
**Depends on:** P13-T3 ✅

---

## 1. Overview

P13-T3 delivered the persistent broker daemon and its Unix-socket multi-client transport.
P13-T4 delivers the **short-lived proxy process** that MCP clients (Cursor, Claude, Codex) launch instead of the direct wrapper. The proxy:

1. Optionally spawns the broker if it is not already running (`--broker-spawn`)
2. Connects to the broker over the Unix domain socket
3. Bridges the MCP client's stdio ↔ broker socket bidirectionally
4. Exits cleanly when the client disconnects **without killing the broker**

Clients require only a one-line config change: replace `mcpbridge-wrapper` with `mcpbridge-wrapper --broker-connect`.

---

## 2. Scope

### In-scope
- Full implementation of `BrokerProxy.run()` in `src/mcpbridge_wrapper/broker/proxy.py`
- `--broker-connect` CLI flag: proxy mode (broker must already be running)
- `--broker-spawn` CLI flag: spawn broker if not running, then proxy
- CLI arg parsing for broker flags in `__main__.py` (following `_parse_webui_args` pattern)
- Unit tests in `tests/unit/test_broker_proxy.py` covering proxy connect/disconnect/reconnect
- Updated `SPECS/INPROGRESS/next.md` and `SPECS/Workplan.md` (done at archive time)

### Out-of-scope
- Integration tests with live broker (P13-T5)
- Documentation updates (P13-T6)
- Windows named-pipe support

---

## 3. Design

### 3.1 BrokerProxy.run() internals

```
stdin  ──►  _stdin_to_socket()  ──►  socket writer
socket ──►  _socket_to_stdout()  ──►  stdout
```

Both coroutines run concurrently via `asyncio.gather`.
When **either** side reaches EOF, `run()` cancels the other task and returns — the **socket is closed but the broker process is not signalled**.

Reconnect: If the socket read loop raises `ConnectionResetError`/`BrokenPipeError` before stdin EOF and `_reconnect` is `True`, the proxy waits up to `connect_timeout` seconds for the socket to reappear (broker RECONNECTING), then reconnects.

### 3.2 Connection lifecycle

```
BrokerProxy.run()
  │
  ├─ _connect()  → asyncio.open_unix_connection(socket_path)
  │                raises FileNotFoundError if socket absent
  │
  ├─ asyncio.gather(_stdin_to_socket, _socket_to_stdout)
  │
  └─ _disconnect()  → writer.close() [broker not signalled]
```

### 3.3 BrokerProxy constructor additions

```python
class BrokerProxy:
    def __init__(
        self,
        config: BrokerConfig,
        *,
        auto_spawn: bool = False,       # --broker-spawn
        connect_timeout: float = 10.0,  # seconds to wait for broker socket
        reconnect: bool = False,        # retry on broken connection
    ) -> None:
```

### 3.4 CLI flags

Two new flags, parsed by `_parse_broker_args()` in `__main__.py`:

| Flag | Behaviour |
|------|-----------|
| `--broker-connect` | Proxy mode: connect to running broker; error if socket absent |
| `--broker-spawn` | Spawn broker if not running, then proxy (implies `--broker-connect`) |

When either flag is present, `main()` constructs a `BrokerProxy` and calls `asyncio.run(proxy.run())` instead of the existing `create_bridge()` path. The legacy direct mode is the **default** when neither flag is present.

### 3.5 Spawn helper

`_spawn_broker_if_needed(config: BrokerConfig) -> None`

- If `config.pid_file` exists and process is alive → no-op (broker already running)
- Otherwise: `subprocess.Popen([sys.executable, "-m", "mcpbridge_wrapper", "--broker-daemon"])` detached (`start_new_session=True`), then poll `config.socket_path` up to `connect_timeout` seconds.
- Note: `--broker-daemon` entry point is a **future task** (P13-T5 or P13-T6). For now, `_spawn_broker_if_needed` documents the expected command but is tested via mocking; actual spawning is validated manually.

---

## 4. File changes

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Full implementation of `BrokerProxy` |
| `src/mcpbridge_wrapper/__main__.py` | Add `_parse_broker_args()` and broker-mode branch in `main()` |
| `tests/unit/test_broker_proxy.py` | New — unit tests for `BrokerProxy` |
| `tests/unit/test_broker_stubs.py` | Update stub test to reflect no longer raising `NotImplementedError` |

---

## 5. Acceptance criteria

- [x] `BrokerProxy.run()` no longer raises `NotImplementedError`
- [ ] Proxy connects to an already-running broker via Unix socket and forwards messages both ways
- [ ] Proxy exits without signalling/killing the broker when stdin reaches EOF
- [ ] `--broker-connect` flag is accepted; unrecognised flags pass through to legacy bridge path
- [ ] `--broker-spawn` implies `auto_spawn=True`
- [ ] Legacy direct mode (no broker flags) is unaffected
- [ ] Unit tests cover: connect success, connect timeout, EOF handling, broken connection with `reconnect=False`
- [ ] All quality gates pass

---

## 6. Quality gates

- `pytest` — all tests pass
- `ruff check src/` — no errors
- `mypy src/` — no new errors
- `pytest --cov` — coverage ≥ 90%
