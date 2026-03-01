# P2-T1 Validation Report

**Task:** Replace --broker-spawn/--broker-connect with single --broker flag
**Date:** 2026-03-01
**Verdict:** PASS

## Acceptance Criteria

- [x] `--broker` flag auto-connects when daemon is alive, spawns when absent (via existing `BrokerProxy.auto_spawn=True` logic from P2-T2)
- [x] `--broker-spawn` and `--broker-connect` still work unchanged (no existing tests modified; all 678 pass)
- [x] All MCP settings examples in README use `--broker` (Cursor, Claude Code, Codex CLI sections updated)
- [x] All existing tests pass (678 passed, 2 warnings, 0 failures)
- [x] New tests for `--broker` flag pass (4 new tests added)

## Changes Made

### `src/mcpbridge_wrapper/__main__.py`
- `_parse_broker_args`: added `elif arg == "--broker"` branch — sets `broker_spawn = True` and `broker_connect = True`, identical to `--broker-spawn`
- Docstring updated to describe `--broker` as the recommended flag, `--broker-spawn`/`--broker-connect` as legacy aliases

### `README.md`
- Quick-start Cursor JSON example (×2): `--broker-spawn` → `--broker`
- Broker Mode reference section: replaced single-line `--broker-spawn` note with three-line description of `--broker` (recommended), `--broker-connect` (legacy), `--broker-spawn` (legacy alias)
- Quick migration examples for Claude Code and Codex CLI: `--broker-connect` → `--broker`
- Multi-Agent guidance: `--broker-spawn --web-ui` → `--broker --web-ui`
- Cursor Configuration section (×2): `--broker-spawn` → `--broker`
- Claude Code section (×2): `--broker-spawn` → `--broker`
- Codex CLI section (×2): `--broker-spawn` → `--broker`

### `tests/unit/test_main.py`
- `TestParseBrokerArgs`: added `test_broker_flag_sets_spawn_and_connect` and `test_broker_flag_not_forwarded_to_bridge`
- `TestMainBrokerMode`: added `test_main_broker_flag_sets_auto_spawn` and `test_main_broker_flag_success`

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/unit/` | 678 passed, 2 warnings |
| `ruff check src/` | All checks passed |
| `pytest --cov` | 91.41% (≥ 90% required) |
