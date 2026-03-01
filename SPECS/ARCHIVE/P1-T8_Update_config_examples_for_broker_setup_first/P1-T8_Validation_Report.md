# Validation Report: P1-T8 — Update /config examples for broker setup first

**Date:** 2026-03-01  
**Verdict:** PASS

## Summary

Updated client configuration templates under `config/` so broker-mode setup appears first for Cursor, Zed, Claude Code, and Codex CLI examples.

## Delivered Changes

- `config/cursor-mcp.json`
  - Added broker-first option blocks (`_option1_uvx_broker`, `_option1b_uvx_broker_web_ui`).
  - Shifted non-broker options to `_option2*` and below.
- `config/zed-agent.json`
  - Added broker-first option blocks (`_option1_uvx_broker`, `_option1b_uvx_broker_web_ui`).
  - Shifted non-broker options to `_option2*` and below.
- `config/claude-code.txt`
  - Added broker-mode command as `OPTION 1` and broker + Web UI as `OPTION 1B`.
  - Moved non-broker alternatives to `OPTION 2` and below.
- `config/codex-cli.txt`
  - Added broker-mode command as `OPTION 1` and broker + Web UI as `OPTION 1B`.
  - Moved non-broker alternatives to `OPTION 2` and below.

## Acceptance Criteria Check

- [x] `config/cursor-mcp.json` presents a broker-mode option first in `xcode-tools` options.
- [x] `config/zed-agent.json` presents a broker-mode option first in `xcode-tools` options.
- [x] `config/claude-code.txt` lists a broker setup command before non-broker options.
- [x] `config/codex-cli.txt` lists a broker setup command before non-broker options.
- [x] Full quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (>= 90%).

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

## Notes

- Initial `pytest` run failed due to environment import setup (`ModuleNotFoundError: mcpbridge_wrapper`).
- Resolved by installing the package in editable mode with `python3 -m pip install -e .`, then re-running quality gates successfully.
