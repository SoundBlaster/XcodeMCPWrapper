# Validation Report: P2-T6 — Remove legacy --broker-connect and --broker-spawn flags

**Date:** 2026-03-01  
**Verdict:** PASS

## Summary

Removed legacy broker aliases from runtime broker-flag parsing and aligned docs/templates to a two-flag model:
- `--broker` for proxy mode
- `--broker-daemon` for explicit host mode

Legacy flags are no longer consumed as broker control flags; they are forwarded as ordinary passthrough args.

## Delivered Changes

- Updated broker argument parsing and broker-related docstrings in:
  - `src/mcpbridge_wrapper/__main__.py`
  - `src/mcpbridge_wrapper/broker/proxy.py`
- Updated parser/main unit tests to reflect removed alias behavior:
  - `tests/unit/test_main.py`
  - `tests/unit/test_broker_proxy.py`
- Removed legacy alias guidance/examples from user docs + DocC mirrors:
  - `README.md`
  - `docs/broker-mode.md`
  - `docs/cursor-setup.md`
  - `docs/claude-setup.md`
  - `docs/codex-setup.md`
  - `docs/webui-setup.md`
  - `docs/troubleshooting.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/CursorSetup.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/ClaudeCodeSetup.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md`
  - `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md`
- Updated broker config templates to `--broker`-only examples:
  - `config/cursor-mcp-broker.json`
  - `config/claude-code-broker.txt`
  - `config/codex-cli-broker.txt`

## Acceptance Criteria Check

- [x] Wrapper no longer accepts `--broker-connect` and `--broker-spawn` as broker control flags.
- [x] Broker-mode docs no longer present aliases as usable/recommended options.
- [x] Broker guidance remains clear for `--broker` (proxy) and `--broker-daemon` (host).
- [x] Quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Quality Gates

1. `pytest`
- Result: PASS
- Evidence: `735 passed, 5 skipped`

2. `ruff check src/`
- Result: PASS
- Evidence: `All checks passed!`

3. `mypy src/`
- Result: PASS
- Evidence: `Success: no issues found in 18 source files`

4. `pytest --cov`
- Result: PASS
- Evidence: `Required test coverage of 90.0% reached. Total coverage: 91.26%`

## Additional Verification

- Legacy flag reference sweep outside archival/spec artifacts reduced to intentional parser-forwarding tests only.
- Targeted parser/broker tests passed:
  - `tests/unit/test_main.py::TestParseBrokerArgs`
  - `tests/unit/test_main.py::TestMainBrokerMode`
  - `tests/unit/test_main.py::TestMainWebUIBrokerFlagCompatibility`
  - `tests/unit/test_broker_proxy.py::TestParseBrokerArgs`

## Notes

Given this is a pre-release compatibility cleanup, external users should configure broker mode with `--broker` only.
