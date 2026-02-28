# PRD: FU-P13-T17 — Enable broker-hosted Web UI with shared multi-client telemetry

## 1. Objective

Deliver a single-host broker topology where one long-lived broker process can also host the Web UI dashboard and expose telemetry aggregated across all broker-connected agents. This closes the current behavior gap where broker paths are transport-only and do not start dashboard services.

The implementation must support:
- `--broker-daemon --web-ui [--web-ui-config|--web-ui-port]` in one process
- `--broker-spawn --web-ui ...` propagating Web UI args to the spawned daemon host
- broker-side telemetry recording for `initialize` and `tools/call` lifecycles so all broker clients appear in one metrics/audit stream

## 2. Success Criteria and Acceptance Tests

### Success Criteria
- Broker daemon can start Web UI server when requested without entering direct-mode bridge loop.
- Auto-spawn proxy can bootstrap a broker host with Web UI enabled from the same client config.
- Shared dashboard reflects tool requests/responses from multiple broker clients.
- Existing direct-mode and broker-only behavior remains backward compatible.

### Acceptance Tests
- Unit test: `main()` broker-daemon + `--web-ui` starts server thread and wires telemetry store into broker transport.
- Unit test: `main()` broker-spawn + `--web-ui` passes spawn args to `BrokerProxy` and includes Web UI flags.
- Unit test: `UnixSocketServer` records request/response telemetry and client identity on broker-routed traffic.
- Regression: existing broker tests and Web UI tests remain green.

## 3. Test-First Plan

1. Add failing unit tests first for new broker-daemon Web UI branch behavior in `tests/unit/test_main.py`.
2. Add failing tests for `BrokerProxy` spawn-arg propagation in `tests/unit/test_broker_proxy.py`.
3. Add failing transport telemetry tests in `tests/unit/test_broker_transport.py`.
4. Implement runtime changes after tests exist.
5. Run required gates:
   - `PYTHONPATH=src pytest`
   - `ruff check src/`
   - `mypy src/`
   - `PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## 4. Execution Plan (Hierarchical TODO)

### Phase A — Broker+WebUI runtime orchestration
- Inputs: `__main__.py` argument parsing and broker mode branches.
- Outputs: broker-daemon mode can initialize Web UI components and start dashboard thread.
- Verification: broker path exits through `asyncio.run(daemon.run_forever())` with Web UI active when requested.

### Phase B — Broker telemetry integration
- Inputs: `broker/transport.py` request/response routing logic.
- Outputs: optional metrics/audit hooks recorded for `initialize` and `tools/call` traffic.
- Verification: request latency/error stats emitted into shared store and audit stream.

### Phase C — Auto-spawn configuration consistency
- Inputs: `broker/proxy.py` spawn command construction.
- Outputs: optional spawn args support so `--broker-spawn --web-ui` uses one shared config story.
- Verification: spawned daemon command contains requested Web UI args.

### Phase D — Validation/reporting
- Inputs: updated code + tests.
- Outputs: `SPECS/INPROGRESS/FU-P13-T17_Validation_Report.md` with PASS/FAIL and gate outputs.
- Verification: acceptance criteria checklist fully resolved.

## 5. Decision Points and Constraints

- Keep Web UI hosting on broker daemon only; do not start dashboard in short-lived `--broker-connect` proxy processes.
- Preserve current stdout protocol behavior: JSON-RPC only, no dashboard logs on stdout.
- Keep feature additive and backward-compatible for existing configs.
- Review subject name: `fu_p13_t17_broker_hosted_webui`.

## 6. Notes (Files likely touched)

- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/broker/transport.py`
- `src/mcpbridge_wrapper/broker/proxy.py`
- `tests/unit/test_main.py`
- `tests/unit/test_broker_proxy.py`
- `tests/unit/test_broker_transport.py`
