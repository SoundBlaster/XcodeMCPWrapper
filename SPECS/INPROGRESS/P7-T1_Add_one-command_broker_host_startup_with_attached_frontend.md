# P7-T1 — Add one-command broker host startup with attached frontend

## Objective Summary

The current explicit broker workflow is operationally correct but too manual:
users must start a dedicated host, ensure the dashboard port is free, confirm
that the dashboard actually belongs to the broker host, and only then launch
the TUI. `P7-T1` should collapse that into one operator-facing command that
starts the recommended dedicated-host topology and immediately opens the
frontend against the same runtime.

The goal is not to invent a third broker mode. The new command should be a thin
orchestration layer over existing primitives: broker daemon startup,
broker-hosted Web UI, and TUI attachment. It must fail early and clearly when
the recommended runtime cannot be established, especially around occupied ports,
non-interactive terminals, or stale broker/dashboard state.

## Deliverables

- Add a one-command startup mode such as `--broker-console` that:
  - validates interactive-terminal requirements
  - starts or reuses the dedicated broker host in the recommended topology
  - ensures the dashboard endpoint is reachable and broker-backed
  - launches the existing TUI against that runtime
- Refactor startup orchestration into reusable helpers instead of duplicating
  broker-daemon, Web UI, and TUI logic inside `main()`.
- Add tests covering success, occupied-port failure, unreachable dashboard,
  stale existing broker, and invalid flag combinations.

## Success Criteria

- Users can run one command and land in a working frontend without manually
  sequencing broker host startup and TUI attachment.
- When startup cannot produce a broker-backed dashboard, the command exits with
  a precise actionable error before dropping the user into a broken TUI.
- The new command preserves existing `--broker-daemon`, `--web-ui`, and `--tui`
  behavior instead of regressing current workflows.

## Test-First Plan

1. Add CLI/main tests that pin the new mode, valid/invalid flag combinations,
   and non-interactive terminal handling.
2. Add orchestration-unit tests for “start host, wait for broker-backed
   dashboard, then run TUI” using mocks around Web UI readiness probes, daemon
   lifecycle helpers, and `run_tui`.
3. Add failure tests for:
   - dashboard port already occupied by a foreign process
   - broker alive without a reachable broker-backed dashboard
   - startup timeout or refused connection while waiting for the dashboard
4. Only after those tests exist, implement the orchestration helpers and wire
   the new mode into `__main__.py`.
5. Run required quality gates: `pytest`, `ruff check src/`, `mypy src/`, and
   `pytest --cov`.

## Execution Plan

### Phase 1: CLI shape and orchestration contract

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- existing parsing/validation for `--tui`, `--broker-daemon`, and `--web-ui`

Outputs:
- exact flag name and compatibility rules for the one-command mode
- helper contract for starting/checking the recommended broker-hosted dashboard

Verification:
- existing modes keep their current validation rules
- the new mode has one predictable entrypoint and one clear failure surface

### Phase 2: Startup and attachment flow

Inputs:
- existing broker-daemon startup path
- existing Web UI runtime preparation and status endpoints
- `src/mcpbridge_wrapper/tui.py` runtime builder and `run_tui`

Outputs:
- orchestration helpers that start or verify the dedicated host
- readiness probe that confirms `/api/health` and `/api/broker/status`
- TUI launch path that attaches only after the runtime is known-good

Verification:
- successful startup reaches the same broker-backed dashboard the TUI targets
- failures on port ownership or missing broker status do not drop into a broken
  TUI session

### Phase 3: Hardening, tests, and operator messaging

Inputs:
- orchestration implementation
- main/TUI test suites

Outputs:
- tests for success and common degraded states
- concise stderr guidance for remediation when the one-command path cannot
  establish the recommended runtime
- validation report with required quality-gate results

Verification:
- startup messages tell the user exactly whether broker, dashboard, and TUI are
  ready
- quality gates remain green with project coverage still above threshold

## Acceptance Tests

- `pytest tests/unit/test_main_tui.py`
- `pytest tests/unit/test_tui.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer a new orchestration mode over changing `--tui` semantics; `--tui`
  should remain “attach to existing dashboard” unless explicitly told to manage
  lifecycle.
- Reuse the broker-hosted dashboard status API as the readiness gate rather than
  inventing another side channel for the frontend.
- Treat “dashboard reachable but not broker-backed” as a hard failure for this
  mode, because the whole point is to guarantee the recommended topology.

## Notes

- Keep docs mostly deferred to `P7-T5`, aside from any required CLI help text
  and inline error wording needed for correctness.
- The follow-up task `P7-T2` can build on any orchestration/readiness helpers
  introduced here; avoid burying them inside curses-only code.
- Review subject name for this task: `broker_console_startup`.
