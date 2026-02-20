# Validation Report: BUG-T15

## Scope
Investigate and harden behavior when MCP config passes both `--web-ui-port` and `--web-ui-config`.

## Implemented Changes
- Added explicit stderr note when CLI port overrides config port.
- Added explicit hint on port-collision path when both flags are present.
- Added unit tests for precedence note and combined-flags collision hint.
- Updated Web UI setup docs to prefer config-driven port with `--web-ui-config` and document precedence.

## Quality Gates
- `pytest`: PASS (628 passed, 5 skipped)
- `ruff check src/`: PASS
- `mypy src/`: PASS
- `pytest --cov`: PASS (91.39% total coverage, threshold 90%)

## Regression Coverage Added
- `tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_port_and_config_logs_precedence_note`
- `tests/unit/test_main_webui.py::TestPortCollisionHandling::test_occupied_port_with_port_and_config_shows_hint`

## Outcome
BUG-T15 behavior is now diagnosable at runtime and documentation no longer promotes the ambiguous combined MCP example. Users can identify when forced CLI port selection causes Web UI startup to be skipped.
