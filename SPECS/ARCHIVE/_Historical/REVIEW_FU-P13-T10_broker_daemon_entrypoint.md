## REVIEW REPORT — FU-P13-T10: broker_daemon_entrypoint

**Scope:** FU-P13-T10 implementation commits on `claude/implement-flow-run-skill-d6MCw`
**Files changed:** 4 (src/mcpbridge_wrapper/__main__.py, tests/unit/test_broker_proxy.py, tests/unit/test_main.py, docs/broker-mode.md)
**Date:** 2026-02-19

---

### Summary Verdict

- [x] **Approve with comments**

No blockers. Implementation is correct, minimal, and well-tested. Two low-severity observations noted below.

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `main()` docstring does not mention `--broker-daemon`**

`src/mcpbridge_wrapper/__main__.py:258`

The docstring lists `--web-ui`, `--broker-connect`, `--broker-spawn` but omits the new `--broker-daemon` flag. This is cosmetic but will mislead readers of the docstring who try to understand supported modes.

*Suggested fix:* Add `--broker-daemon` to the docstring's flag list, e.g.:

```
Supports optional --broker-daemon flag to start a persistent broker host.
Supports optional --broker-connect / --broker-spawn flags for proxy mode.
```

**[Low] Web UI args are parsed unconditionally before `--broker-daemon` early-exit**

`src/mcpbridge_wrapper/__main__.py:265-277`

`_parse_webui_args()` runs on every invocation including `--broker-daemon` mode. In broker daemon mode the web UI args are immediately discarded (daemon branch exits before web UI init). This causes a trivial but unnecessary `ValueError` risk if, say, a `--web-ui-port` value is also passed alongside `--broker-daemon`. The current test suite does not cover this combination.

This is a minor structural issue — the existing code convention consistently parses web UI args first — and is not urgent. The risk is low because `--broker-daemon` + `--web-ui-*` is not a documented combination.

*Suggested fix (optional):* Either document that `--broker-daemon` ignores web UI flags, or reorder: check for `--broker-daemon` before `_parse_webui_args()`. Not filed as a blocking follow-up.

---

### Architectural Notes

- The 4-tuple return from `_parse_broker_args()` is a clean backward-compatible extension. All callers in tests have been updated correctly.
- Wiring `daemon._transport = transport` directly before `asyncio.run(daemon.run_forever())` is the same pattern shown in the BrokerDaemon constructor signature and documented in broker architecture spec. Consistent with existing usage.
- `BrokerDaemon.run_forever()` handles SIGTERM/SIGINT internally via `loop.add_signal_handler()`, so no additional signal handling is needed in `main()`. Correct.
- The early-return pattern (daemon mode → proxy mode → direct mode) keeps the three modes mutually exclusive at the entry point. Clean.

---

### Tests

- 22 existing + new tests pass for broker-related parsing and daemon mode.
- 5 new `TestMainBrokerDaemonMode` tests cover: success, KeyboardInterrupt, RuntimeError, no bridge started, transport wired.
- 2 new `TestParseBrokerArgs` tests in both test files cover `--broker-daemon` flag isolation and non-leak.
- Pre-existing test failures (23 total) are unrelated to this change and confirmed unchanged.
- Integration test for live `--broker-spawn` end-to-end was deferred (Linux/no macOS, no `xcrun mcpbridge` available).

---

### Next Steps

1. (Optional, Low) Update `main()` docstring to list `--broker-daemon`.
2. (P1) FU-P13-T11: Preserve JSON-RPC numeric request ID fidelity in broker transport.
3. (P1) FU-P13-T12: Enforce Unix-socket security boundary for broker clients.
4. (P1) FU-P13-T13: Make broker startup transactional on transport bind failure.
5. (P1) FU-P13-T14: Complete interactive Xcode prompt verification.
