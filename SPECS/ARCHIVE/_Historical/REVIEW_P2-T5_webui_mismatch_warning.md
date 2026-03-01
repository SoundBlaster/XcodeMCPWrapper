## REVIEW REPORT — P2-T5: Web UI mismatch warning

**Scope:** origin/main..HEAD
**Files:** 3 changed (proxy.py, __main__.py, test_broker_proxy.py)
**Date:** 2026-03-01

### Summary Verdict
- [x] Approve with comments
- [ ] Approve
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] TCP probe is synchronous and blocks the event loop for up to 0.5 s**

`_warn_web_ui_mismatch()` calls `socket.connect()` synchronously. While 0.5 s is a short
wall-clock time, it blocks the asyncio event loop for the full timeout duration when the port
is not listening. For a single-proxy use case this is negligible, but it is architecturally
inconsistent with the rest of the proxy code, which is fully async.

**Suggested future fix (optional):** Wrap the probe in `asyncio.wait_for(loop.run_in_executor(...), timeout=0.5)`.
Not a blocker — the current behaviour is functionally correct and the window is bounded.

**[Low] Hardcoded default port 8080 in `__main__.py`**

The default web UI port (8080) is defined inline in `main()` rather than referencing the
canonical default from `WebUIConfig`. If the default ever changes in `WebUIConfig`, the
proxy's mismatch probe would silently use the wrong port.

**Suggested future fix (optional):** Extract `_WEB_UI_DEFAULT_PORT` as a module-level constant
or import it from `webui.config`. Not a blocker — current value matches.

**[Nit] `_new_broker_spawned` is an instance variable set in a helper method**

Setting `self._new_broker_spawned = True` inside `_spawn_broker_if_needed()` creates a hidden
state dependency. The attribute is initialized in `__init__` to `False`, so the default is
safe, but it's not immediately obvious from reading `run()` that the flag is set as a side
effect. A comment in `run()` pointing to the flag's setter is sufficient (already present).

---

### Architectural Notes

- The TCP probe approach is pragmatic: no new infrastructure (no status file, no broker status
  endpoint) required. The only assumption is that the web UI is on `127.0.0.1:{port}`, which
  matches all current deployment scenarios.
- `_new_broker_spawned` correctly prevents false-positive warnings when the proxy just spawned
  a new daemon — the HTTP server may not be ready, but `--web-ui` was already passed in
  `spawn_args`.
- The warning is stderr-only; the JSON-RPC stream is unaffected. Session continues normally.

---

### Tests

- Added `TestBrokerProxyWebUIMismatch` (5 tests):
  - `test_warning_printed_when_port_refused` — probe fails → warning in stderr
  - `test_no_warning_when_port_listening` — probe succeeds → no warning
  - `test_no_warning_when_new_broker_spawned` — spawned → probe skipped
  - `test_no_warning_when_web_ui_port_not_set` — port=None → no probe, no warning
  - `test_warning_is_actionable` — warning text contains `broker.sock` / `Restart`
- Coverage: 91.66% (≥ 90%). ✅
- All 737 tests pass. ✅

---

### Next Steps

- **Optional FU:** Make TCP probe async (`run_in_executor`) to avoid blocking the event loop.
  Low priority — 0.5 s is acceptable for the one-time startup path.
- **Optional FU:** Centralise default web UI port constant to avoid divergence with
  `WebUIConfig._DEFAULTS["port"]`.

**VERDICT: PASS — no blockers; two low-severity and one nit observation.**
