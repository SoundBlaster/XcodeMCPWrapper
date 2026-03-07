# P6-T2 — Build a terminal frontend for broker daemon monitoring and control

## Objective Summary

Broker mode now has an explicit runtime-status surface through the broker-hosted
Web UI API, but operators still need to open a browser or tail `broker.log` to
understand whether the shared daemon is healthy. This task adds a terminal-first
frontend that makes broker health visible from one command. The frontend should
work as an operator tool, not as another MCP client: it must show the broker's
lifecycle state, core runtime identifiers, active-client count, and recent
reconnect/error signals, and it must expose at least one daemon control action.

The implementation should not add a heavy TUI framework unless the existing
stdlib capabilities are clearly insufficient. The project currently ships only
base and optional Web UI dependencies, so the frontend should prefer a
dependency-free approach that reads the broker's local state, optionally calls
the local Web UI status API when available, and renders a live terminal screen
with simple key controls.

## Deliverables

- Add a broker terminal frontend module under `src/mcpbridge_wrapper/` that
  renders a live terminal view and can be launched from the main CLI.
- Add CLI wiring for a dedicated operator flag (for example `--broker-tui`)
  without disturbing existing direct, broker, or Web UI modes.
- Show broker lifecycle status, daemon/upstream PID information, connected
  client count, and recent broker event/reconnect indicators in the UI.
- Expose at least one explicit lifecycle control from the TUI, with stop as the
  minimum acceptable action.
- Add automated tests covering argument parsing, state snapshot/rendering, and
  main-branch CLI wiring for the terminal frontend.

## Success Criteria

- Users can launch a terminal UI directly from the wrapper package to inspect
  broker runtime state without manually tailing `~/.mcpbridge_wrapper/broker.log`.
- The UI shows, at minimum, broker state, daemon PID, upstream PID when known,
  connected client count, and recent reconnect/error indicators.
- The UI exposes at least one daemon lifecycle control action and handles the
  action safely with clear terminal feedback.
- The solution does not require introducing a new third-party TUI dependency.

## Test-First Plan

1. Add unit tests for a new terminal frontend snapshot/renderer module so the
   expected output sections are fixed before CLI wiring.
2. Add tests for broker-argument parsing and `main()` behavior around the new
   terminal frontend flag, including isolation from other broker-only commands.
3. Add tests for the control path so the TUI can request broker shutdown
   without duplicating fragile signal logic inline.
4. Implement production code only after the expected snapshot/render/control
   contracts are pinned in tests.
5. Run the required quality gates: `pytest`, `ruff check src/`, `mypy src/`,
   and `pytest --cov`.

## Execution Plan

### Phase 1: Define terminal frontend data sources and command contract

Inputs:
- `src/mcpbridge_wrapper/__main__.py` broker lifecycle branches
- `src/mcpbridge_wrapper/broker/types.py` default state paths
- `src/mcpbridge_wrapper/webui/config.py` and `/api/broker/status` contract
- `docs/broker-mode.md` operational expectations for logs, status, and stop

Outputs:
- Final CLI flag and launch contract for the terminal frontend
- Snapshot model describing broker state, API availability, and recent events
- Decision on how the frontend discovers Web UI host/port/auth vs local files

Verification:
- The frontend can operate even when the browser dashboard is not open
- Existing broker lifecycle commands remain separate and backward-compatible

### Phase 2: Implement terminal frontend module and CLI wiring

Inputs:
- Broker status/control helpers in `src/mcpbridge_wrapper/__main__.py`
- Broker runtime status API and local broker state files

Outputs:
- New terminal frontend module with:
  - snapshot collection
  - terminal rendering
  - simple key handling / refresh loop
  - stop control integration
- `main()` wiring for the new launch flag

Verification:
- A user can run one command and get a refreshing terminal dashboard
- The stop control exits cleanly and reports result in the terminal

### Phase 3: Lock behavior with tests and validation

Inputs:
- New frontend module
- Updated `main()` and parsing logic
- Unit tests for terminal rendering/control behavior

Outputs:
- Passing unit tests for CLI/TUI behavior
- Validation report with full quality-gate results

Verification:
- The terminal frontend is covered without relying on an interactive real TTY
- Coverage remains at or above the repository threshold

## Acceptance Tests

- `pytest tests/unit/test_main.py -k broker_tui`
- `pytest tests/unit/test_broker_tui.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Use a stdlib terminal loop with ANSI screen clears and non-blocking key reads
  instead of introducing `textual`, `rich`, or another new UI dependency.
- Treat the broker-hosted Web UI API as the richest optional data source, but
  keep local PID/socket/version/log inspection as a fallback so the frontend is
  still useful when the dashboard is unavailable.
- Reuse or extract broker stop logic from `__main__.py` rather than duplicating
  signal-handling code in the terminal frontend.
- Review subject name for this task: `broker_terminal_frontend`.

## Notes

- User-facing documentation updates for the dedicated-host workflow belong in
  `P6-T3`, unless a small inline CLI help note is required for correctness.
- Keep the first iteration deliberately narrow: live status + recent events +
  one control action are enough to satisfy the operator need without turning
  this task into a full dashboard rewrite.
