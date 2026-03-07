# P6-T2 — Build a terminal frontend for broker daemon monitoring and control

## Objective Summary

Users who adopt the dedicated broker host pattern still need a first-class
operator surface that does not require a browser. This task adds a standalone
terminal frontend that attaches to the existing broker-hosted Web UI, reads the
broker runtime status API introduced in `P6-T1`, and presents broker health in
one explicit place. The frontend should make it obvious whether the shared
daemon is healthy, reconnecting, awaiting approval, or no longer reachable.

The implementation should stay dependency-light. Prefer the Python standard
library (`curses`, `urllib`, `json`) and existing `WebUIConfig` loading over a
new third-party terminal framework. The TUI may require an already running
broker-hosted Web UI; that constraint is acceptable as long as failure modes are
clear and actionable.

## Deliverables

- Add a standalone `--tui` runtime mode that launches an interactive terminal
  dashboard instead of proxy, bridge, or daemon execution.
- Implement a TUI module that polls `GET /api/broker/status`, inspects control
  capability, and renders broker state, PID information, connected client
  counts, readiness flags, and reconnect indicators.
- Surface recent broker activity by tailing the recommended local
  `~/.mcpbridge_wrapper/broker.log` file inside the terminal UI.
- Expose at least one lifecycle control action from the TUI, with `stop` backed
  by `POST /api/control/stop`.
- Add automated tests for argument parsing, HTTP/status handling, and terminal
  rendering/control logic.

## Success Criteria

- Users can run `mcpbridge-wrapper --tui` to inspect broker status without
  tailing logs manually.
- The terminal UI shows broker state, daemon PID, upstream PID, connected
  client count, readiness/cached-tool status, and reconnect attempt count.
- The UI displays recent broker log lines or equivalent reconnect indicators in
  the same screen.
- The UI exposes an explicit stop control and handles unavailable/unauthorized
  backends with clear messaging.
- No new runtime dependency is required for the terminal frontend.

## Test-First Plan

1. Add parser/main tests that lock down `--tui` mode, including invalid
   flag combinations with `--broker*` and `--web-ui`.
2. Add unit tests for a pure rendering/presentation layer so the terminal
   layout is testable without a real curses session.
3. Add client tests for status fetches, stop requests, auth header behavior,
   and log tail handling using mocks or a lightweight HTTP stub.
4. Implement the production TUI only after the expected runtime contract and
   screen sections are pinned in tests.
5. Run required quality gates: `pytest`, `ruff check src/`, `mypy src/`,
   and `pytest --cov`.

## Execution Plan

### Phase 1: Standalone TUI mode and configuration

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/webui/config.py`
- existing broker/Web UI CLI flag behavior

Outputs:
- `--tui` argument parsing and validation
- Web UI endpoint resolution for host, port, and optional auth credentials
- clear errors for unsupported flag combinations

Verification:
- `main()` routes cleanly into TUI mode
- `--tui` does not accidentally start bridge, proxy, or broker-daemon codepaths

### Phase 2: Terminal frontend runtime

Inputs:
- `GET /api/broker/status`
- `POST /api/control/stop`
- broker log path conventions from `BrokerConfig.default()`

Outputs:
- new `src/mcpbridge_wrapper/tui.py` module
- polling client + screen model + curses runner
- keyboard actions for refresh, quit, and stop

Verification:
- healthy and degraded states render distinct operator-facing output
- unreachable backend and auth failures produce actionable terminal messages

### Phase 3: Validation and integration hardening

Inputs:
- TUI runtime implementation
- parser/main tests and pure rendering tests

Outputs:
- unit test coverage for TUI rendering, HTTP control, and CLI wiring
- validation report with required quality gate results

Verification:
- the TUI remains dependency-free and CI-stable
- quality gates remain green with coverage at or above project threshold

## Acceptance Tests

- `pytest tests/unit/test_tui.py`
- `pytest tests/unit/test_main_tui.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- The TUI should be a standalone mode (`--tui`), not a secondary view embedded
  into `--broker-daemon`, so operator lifecycle stays explicit and predictable.
- The TUI should consume the existing broker-hosted Web UI APIs rather than
  opening the broker socket directly; that keeps one runtime contract for both
  browser and terminal frontends.
- Recent activity should come from the recommended local `broker.log` tail. The
  status API already covers health, while the log tail adds human-readable event
  context without expanding the HTTP schema again in `P6-T2`.

## Notes

- Keep user-facing documentation mostly scoped to `P6-T3`, aside from any small
  inline CLI/help text needed for correctness.
- Prefer pure helper functions for layout and formatting so the curses shell is
  thin and easy to test.
- Review subject name for this task: `broker_terminal_frontend`.
