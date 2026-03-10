# Web UI Dashboard Rebuild Workplan

## Assumptions

- Rebuild execution happens on branch `codex/rebuild-p10-t1-web-ui`.
- Existing Web UI functionality is baseline behavior and cannot regress.
- Quality gates remain: `pytest`, `ruff check`, `mypy`, and targeted Web UI tests.

## Phases Overview

| Phase | Goal | Exit Criteria |
|---|---|---|
| PH-1 | Establish explicit contracts and baselines | Contracts documented, compatibility tests defined |
| PH-2 | Refactor architecture behind stable interfaces | Runtime no longer relies on type-ignore for metrics wiring |
| PH-3 | Close known bugs and contract gaps | Bug fixes validated and documented |
| PH-4 | Parity proof and release readiness | Compatibility harness green, docs aligned |

## Tasks

### PH-1 - Contracts and Baseline

#### T-001 (P0): Define telemetry and API contracts
- Deps: none
- Parallelizable with: none
- Touched files:
  - `src/mcpbridge_wrapper/webui/contracts.py`
  - `tests/unit/webui/test_contracts.py`
- Acceptance criteria:
  - Metrics summary and timeseries contracts are explicit and versioned in code.
  - Tests fail on response shape drift.
- Verification commands:
  - `pytest tests/unit/webui/test_contracts.py -v`
  - `mypy src/`
- Rollback:
  - Remove new contract module and revert imports to current direct typing.

#### T-002 (P0): Capture compatibility golden payloads
- Deps: T-001
- Parallelizable with: none
- Touched files:
  - `tests/fixtures/webui/metrics_summary.json`
  - `tests/fixtures/webui/metrics_timeseries.json`
  - `tests/fixtures/webui/audit_page.json`
- Acceptance criteria:
  - Golden fixtures generated from current baseline behavior.
  - Contract tests compare runtime output with golden keys and value types.
- Verification commands:
  - `pytest tests/unit/webui/test_server.py -v`
- Rollback:
  - Remove fixtures and fixture-based assertions.

### PH-2 - Architecture Refactor

#### T-003 (P0): Introduce metrics protocol abstraction
- Deps: T-001
- Parallelizable with: T-004
- Touched files:
  - `src/mcpbridge_wrapper/webui/contracts.py`
  - `src/mcpbridge_wrapper/webui/metrics.py`
  - `src/mcpbridge_wrapper/webui/shared_metrics.py`
  - `src/mcpbridge_wrapper/webui/server.py`
  - `src/mcpbridge_wrapper/__main__.py`
- Acceptance criteria:
  - Both metrics backends satisfy one protocol/interface.
  - `# type: ignore[arg-type]` for metrics server startup is removed.
- Verification commands:
  - `mypy src/`
  - `pytest tests/unit/webui/test_metrics.py tests/unit/webui/test_shared_metrics.py -v`
- Rollback:
  - Revert to pre-refactor wiring and restore existing typing.

#### T-004 (P1): Normalize summary semantics across metrics backends
- Deps: T-003
- Parallelizable with: T-005
- Touched files:
  - `src/mcpbridge_wrapper/webui/shared_metrics.py`
  - `tests/unit/webui/test_shared_metrics.py`
- Acceptance criteria:
  - Shared metrics summary fields match documented semantics (uptime and latency stats).
  - Percentile fields are either exact or explicitly documented approximations.
- Verification commands:
  - `pytest tests/unit/webui/test_shared_metrics.py -v`
- Rollback:
  - Restore current summary query behavior.

### PH-3 - Bug Fixes and Hardening

#### T-005 (P0): Fix authenticated WebSocket live-update path
- Deps: T-003
- Parallelizable with: T-004
- Touched files:
  - `src/mcpbridge_wrapper/webui/server.py`
  - `src/mcpbridge_wrapper/webui/static/dashboard.js`
  - `tests/unit/webui/test_server.py`
- Acceptance criteria:
  - Auth-enabled dashboards receive websocket `metrics_update` events without manual URL token hacks.
  - Non-auth mode behavior remains unchanged.
- Verification commands:
  - `pytest tests/unit/webui/test_server.py -v`
  - `pytest tests/integration/webui/test_e2e.py -v`
- Rollback:
  - Revert websocket auth changes and keep polling fallback.

#### T-006 (P1): Harden CLI validation for Web UI args
- Deps: T-003
- Parallelizable with: T-005
- Touched files:
  - `src/mcpbridge_wrapper/__main__.py`
  - `tests/unit/test_main.py`
- Acceptance criteria:
  - Invalid ports/config args fail with controlled, user-readable errors.
  - No uncaught `ValueError` for malformed CLI input.
- Verification commands:
  - `pytest tests/unit/test_main.py -v`
- Rollback:
  - Restore current parser behavior.

#### T-007 (P1): Align operator documentation and runtime config semantics
- Deps: T-006
- Parallelizable with: none
- Touched files:
  - `docs/webui-setup.md`
  - `README.md`
- Acceptance criteria:
  - Environment variable docs match actual runtime support.
  - Troubleshooting section includes auth-mode websocket behavior.
- Verification commands:
  - `pytest tests/ -v`
  - `make doccheck`
- Rollback:
  - Revert documentation updates.

### PH-4 - Parity and Release Readiness

#### T-008 (P0): Build compatibility harness tests
- Deps: T-002, T-005, T-006
- Parallelizable with: T-009
- Touched files:
  - `tests/integration/webui/test_compat_harness.py`
  - `tests/fixtures/webui/*.json`
- Acceptance criteria:
  - Harness verifies parity for metrics, timeseries, audit, and auth behaviors.
  - CI job executes harness by default for Web UI changes.
- Verification commands:
  - `pytest tests/integration/webui/test_compat_harness.py -v`
- Rollback:
  - Remove harness and fixture dependencies.

#### T-009 (P1): Final verification and packaging
- Deps: T-008
- Parallelizable with: none
- Touched files:
  - `FEATURE_REBUILD/*`
  - `SPECS/INPROGRESS/REBUILD-P10-T1_Validation_Report.md`
- Acceptance criteria:
  - Full quality gates pass.
  - Validation report includes command outputs and parity verdict.
- Verification commands:
  - `pytest`
  - `ruff check src/ tests/`
  - `mypy src/`
  - `pytest tests/unit/webui/ tests/integration/webui/ -v`
- Rollback:
  - Revert release-note and packaging metadata changes only.

#### ✅ T-010 (P1): Build Xcode approval observation harness
- Status: ✅ Completed (2026-03-10)
- Deps: none
- Parallelizable with: T-009
- Touched files:
  - `scripts/xcode_approval_harness.py`
  - `tests/unit/test_xcode_approval_harness.py`
  - `docs/troubleshooting.md`
  - `FEATURE_REBUILD/ObservedBehavior.md`
- Acceptance criteria:
  - [x] Harness can execute deterministic MCP handshake scenarios against `xcrun mcpbridge`
    or the wrapper command.
  - [x] Harness logs timestamped send/receive events, EOF, and timeout boundaries so approval
    races can be reconstructed after a run.
  - [x] Harness can hold and replay `initialize`, `notifications/initialized`, `tools/list`,
    `resources/list`, and `prompts/list` steps with configurable delays around manual Xcode
    approval.
  - [x] Harness records whether `notifications/tools/list_changed` is observed after approval.
- Verification commands:
  - `pytest tests/unit/test_xcode_approval_harness.py -v`
  - `python3 scripts/xcode_approval_harness.py --help`
- Rollback:
  - Remove the harness script/tests/docs note and fall back to ad hoc manual probing.

#### ⬜️ T-011 (P1): Emit synthetic broker tools/list_changed on catalog warm-up
- **Description:** Extend the broker so clients can learn that the Xcode tool catalog became
  available after approval even when upstream `xcrun mcpbridge` never emits
  `notifications/tools/list_changed` itself. Reuse the existing broker warm-up probes and
  synthesize a client-facing `tools/list_changed` only when the cached catalog transitions from
  cold to ready or materially changes after reconnect.
- **Priority:** P1
- **Dependencies:** T-010
- **Parallelizable:** no
- **Outputs/Artifacts:**
  - `src/mcpbridge_wrapper/broker/daemon.py`
  - `src/mcpbridge_wrapper/broker/transport.py`
  - `tests/unit/test_broker_daemon.py`
  - `tests/unit/test_broker_transport.py`
  - `SPECS/INPROGRESS/T-011_Emit_synthetic_broker_tools_list_changed_on_catalog_warm-up.md`
  - `SPECS/INPROGRESS/T-011_Validation_Report.md`
- **Acceptance Criteria:**
  - [ ] Broker emits a synthetic `notifications/tools/list_changed` when its internal cached
    `tools/list` transitions from empty/unavailable to a non-empty ready catalog.
  - [ ] Broker re-emits the synthetic notification when reconnect produces a materially changed
    non-empty tool catalog, but does not spam clients on repeated empty retry probes.
  - [ ] Existing `tools/list` readiness gating and cache-hit behavior remain unchanged for
    clients that explicitly call `tools/list`.
  - [ ] Unit tests cover warm-up, reconnect, and no-op retry behavior for the synthetic
    notification path.
  - [ ] Validation notes document whether Cursor/Zed visibly react to the synthetic signal
    without a manual MCP toggle.

## Acceptance Criteria (rolled up)

1. Web UI API and dashboard contracts remain backward-compatible.
2. Web UI mode remains optional and isolated from core wrapper path.
3. Known bugs in auth/live updates, CLI validation, and docs/config mismatch are resolved.
4. Compatibility harness proves parity against baseline fixtures.
5. Quality gates pass with no regressions.

## Verification Commands

- `pytest`
- `pytest tests/unit/webui/ tests/integration/webui/ -v`
- `pytest tests/unit/test_main.py -v`
- `ruff check src/ tests/`
- `mypy src/`
- `make doccheck`

## Definition of Done

- All P0 tasks complete and verified.
- No compatibility contract regressions.
- Documentation updated to match shipped behavior.
- Rebuild artifacts and validation reports committed.

## Risks & Open Questions

- Risk: Refactoring metrics semantics can cause subtle dashboard deltas.
- Risk: WebSocket auth changes can impact existing browser connection expectations.
- Open question: Should websocket auth move to cookie/session model or token query with explicit frontend support?
- Open question: Should shared metrics expose exact percentiles or keep lightweight approximations with explicit labeling?
