# BUG-T3 PRD — webui only dashboard mode

## 1. Context

Users enabling `--web-ui` for MCP debugging can lose dashboard access when MCP bridge startup fails or when the MCP client session exits early. In those cases the process terminates and Safari shows "can't connect to server" for the dashboard URL.

## 2. Goal

Provide an explicit standalone mode that runs only the Web UI server so the dashboard remains reachable during MCP connection diagnostics.

## 3. Scope

In scope:
- Add a CLI argument (`--web-ui-only`) in startup parsing
- Ensure standalone mode starts FastAPI Web UI without launching bridge subprocess
- Keep existing `--web-ui` behavior unchanged for normal MCP wrapper mode
- Add unit tests for parsing and main startup behavior
- Document standalone usage for troubleshooting

Out of scope:
- Changes to MCP protocol transformation behavior
- Changes to Xcode bridge handshake handling
- New dashboard features unrelated to startup mode

## 4. Deliverables

- Updated `src/mcpbridge_wrapper/__main__.py`:
  - Parse `--web-ui-only`
  - Run `run_server(...)` and return in standalone mode
- Updated tests in `tests/unit/test_main_webui.py`
- Updated troubleshooting docs with standalone mode guidance
- Validation report at `SPECS/INPROGRESS/BUG-T3_Validation_Report.md`

## 5. Acceptance Criteria

1. `--web-ui-only` is accepted by argument parser.
2. `--web-ui-only` implies Web UI enabled and honors `--web-ui-port`.
3. In standalone mode, wrapper does not start `create_bridge()` or stdin forwarding threads.
4. Existing non-standalone behavior remains unchanged.
5. Quality gates pass:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov` with coverage >= 90%

## 6. Dependencies

- Existing Web UI server entrypoint (`mcpbridge_wrapper.webui.server:run_server`)
- Existing CLI parser logic in `src/mcpbridge_wrapper/__main__.py`

## 7. Implementation Plan

1. Extend web UI arg parser return shape to include standalone mode flag.
2. Update main startup flow to short-circuit into `run_server(...)` for standalone mode.
3. Add parser and main-path unit tests for standalone mode.
4. Update troubleshooting docs with standalone command examples.
5. Execute required quality gates and capture results.

## 8. Risks and Mitigations

- Risk: starting both thread mode and standalone mode could double-bind ports.
- Mitigation: ensure standalone path returns before any bridge/websocket thread startup.

- Risk: behavior regression in existing `--web-ui` MCP mode.
- Mitigation: keep existing code path intact and covered by current tests.
