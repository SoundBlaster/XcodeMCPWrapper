# Validation Report: P2-T5 — Warn when --web-ui requested but running broker lacks it

**Date:** 2026-03-01
**Status:** PASS

## Changes Delivered

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/proxy.py` | Added `web_ui_port` param and `_new_broker_spawned` flag to `BrokerProxy`; added `_warn_web_ui_mismatch()` helper; added mismatch check call in `run()` after connect; set `_new_broker_spawned=True` in `_spawn_broker_if_needed` before Popen |
| `src/mcpbridge_wrapper/__main__.py` | Pass effective web UI port (`web_ui_port or 8080` when `web_ui_enabled`, else `None`) to `BrokerProxy` |
| `tests/unit/test_broker_proxy.py` | Added `TestBrokerProxyWebUIMismatch` (5 tests) |

## Acceptance Criteria

- [x] When `--web-ui` is passed to proxy but running broker has no web UI, a warning is printed to stderr
- [x] Warning text is actionable (mentions `broker.sock`, `broker.pid`, how to reconnect with `--broker --web-ui`)
- [x] MCP session continues normally despite the warning
- [x] All existing tests pass
- [x] `pytest --cov` coverage ≥ 90% (achieved 91.66%)
- [x] `ruff check src/` passes
- [x] `ruff format --check src/ tests/` passes

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest -q` | 737 passed, 5 skipped |
| `pytest --cov` coverage | 91.66% (≥ 90% required) |
| `ruff check src/` | PASS |
| `ruff format --check src/ tests/` | PASS |

## Implementation Notes

- `_warn_web_ui_mismatch()` is synchronous — it uses `socket.socket` with a 0.5 s timeout
  for a TCP probe to `127.0.0.1:{web_ui_port}`. This cannot block the event loop for more than
  0.5 s and requires no new dependencies.
- The `_new_broker_spawned` flag prevents false-positive warnings immediately after spawning a
  new broker (the HTTP server may not be ready yet). When an existing broker is found (PID file
  alive or socket liveness check passes), the flag remains `False` and the probe runs.
- The default web UI port (8080) is used in `__main__.py` when `--web-ui` is passed but
  `--web-ui-port` is not explicitly set.
- Warning goes to `sys.stderr` only — the JSON-RPC stream on stdout is not affected.
