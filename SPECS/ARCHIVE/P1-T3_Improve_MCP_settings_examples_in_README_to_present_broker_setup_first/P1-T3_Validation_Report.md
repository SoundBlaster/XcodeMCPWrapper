# Validation Report — P1-T3: Improve MCP settings examples in README to present broker setup first

**Date:** 2026-03-01  
**Verdict:** PASS

## Scope

Updated `README.md` configuration examples for Cursor, Claude Code, and Codex CLI so broker-mode setup is shown first, followed by direct/manual alternatives with consistent ordering and labels.

## Deliverables

- `README.md` configuration section updated to broker-first ordering for:
  - Cursor
  - Claude Code
  - Codex CLI
- Consistent section pattern across all three agents:
  - broker mode (recommended)
  - broker mode with Web UI (optional)
  - direct mode alternatives

## Acceptance Criteria Check

- [x] `README.md` presents broker setup before alternative/manual setup in MCP settings examples for Cursor, Claude Code, and Codex CLI
- [x] MCP example sections use consistent wording and ordering so users can follow the broker-first path without ambiguity

## Commands Executed

- `pytest` (baseline environment check)
- `ruff check src/`
- `mypy src/`
- `TMPHOME=$(mktemp -d); HOME="$TMPHOME" PYTHONPATH=src pytest -q`
- `TMPHOME=$(mktemp -d); HOME="$TMPHOME" PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## Results

- `pytest` (baseline): FAIL in local environment due live user broker socket (`~/.mcpbridge_wrapper/broker.sock`) affecting `tests/unit/test_broker_stubs.py::test_run_raises_timeout_when_no_socket`.
- `ruff check src/`: PASS (`All checks passed!`)
- `mypy src/`: PASS (`Success: no issues found in 18 source files`)
- Isolated full test run: PASS (`715 passed, 5 skipped, 2 warnings`)
- Coverage: PASS (`Total coverage: 91.72%`, threshold 90%)

## Notes

- The baseline pytest failure was environmental (existing broker daemon on the workstation), not caused by task changes.
- Running tests with a temporary isolated `HOME` path avoids contamination from live broker runtime files and matches expected test isolation.
- Two deprecation warnings from `websockets.legacy`/`websockets.server.WebSocketServerProtocol` are pre-existing and non-blocking for this documentation-only task.
