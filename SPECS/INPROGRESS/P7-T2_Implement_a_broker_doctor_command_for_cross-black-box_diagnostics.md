# P7-T2 — Implement a broker doctor command for cross-black-box diagnostics

## Objective Summary

The new broker-console flow reduced startup friction, but users still hit
multi-layer failures that are hard to interpret: Python environment mismatch,
stale broker files, a live broker without dashboard, a dashboard port owned by
the wrong process, or a reachable dashboard that is not the dedicated
broker-hosted runtime. `P7-T2` should provide one explicit doctor command that
explains those states in user-facing language and points to the single next
action instead of sending users to `lsof`, `curl`, or raw logs.

The doctor command should build on the status surfaces already introduced for
the TUI and broker daemon rather than inventing a parallel diagnostics stack.
It should classify the visible runtime into actionable buckets, report the
evidence behind that classification, and expose enough detail to help users
understand whether the broken box is Xcode, the IDE-side MCP config, or the
local Python/broker host.

## Deliverables

- Add a dedicated user-facing diagnostics mode such as `--doctor` wired through
  `src/mcpbridge_wrapper/__main__.py`.
- Introduce a reusable diagnostics module that inspects:
  - package/runtime identity and local executable context
  - broker PID/socket/version files and live process state
  - dashboard endpoint health, ownership, and broker-backed status
  - broker runtime payload when the endpoint is broker-backed
- Print concise diagnosis output with one primary status, supporting evidence,
  and the most likely next action.
- Add tests for healthy, broker-without-dashboard, foreign-dashboard-owner,
  and stale-runtime scenarios.

## Success Criteria

- Users can run one command and immediately learn whether broker mode is healthy
  and, if not, what exact remediation step to take next.
- The doctor output distinguishes at least these cases:
  - broker not running
  - broker running without dashboard
  - dashboard alive but not broker-backed
  - port occupied by another listener before broker startup
  - broker/dashboard version or runtime mismatch when observable
- The implementation reuses existing runtime probes where possible so TUI and
  future UX tasks can share the same diagnosis logic.

## Test-First Plan

1. Add CLI tests that pin `--doctor` flag parsing, incompatibilities with
   bridge-only arguments, and exit-code behavior for healthy vs degraded
   diagnoses.
2. Add diagnostics-unit tests that feed mocked local files, PID checks, port
   listeners, and HTTP probe results into the doctor classifier for the core
   runtime buckets.
3. Add rendering tests that ensure output stays actionable and names the exact
   recommended next action for each major failure class.
4. Only after the behavior is pinned, implement the diagnostics module and wire
   it into `main()`.
5. Run required quality gates: `pytest`, `ruff check src/`, `mypy src/`, and
   `pytest --cov`.

## Execution Plan

### Phase 1: Doctor contract and classification model

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- existing broker/TUI helpers for local PID and dashboard probes

Outputs:
- a stable command shape for doctor mode
- diagnosis categories and exit-code policy
- reusable data structures for findings, summary, and next-action guidance

Verification:
- healthy and degraded states map to deterministic summary strings
- the model can represent both local-file evidence and HTTP-probe evidence

### Phase 2: Local and remote probe implementation

Inputs:
- `BrokerConfig.default()` state files
- local PID/port ownership probes
- dashboard `/api/control`, `/api/health`, and `/api/broker/status`

Outputs:
- consolidated probe helpers for local broker state
- dashboard ownership checks that distinguish “wrong service” from
  “broker-backed but degraded”
- Xcode/upstream status surfaced when the broker-backed dashboard is reachable

Verification:
- no-shell-debugging scenarios from the workplan can be distinguished from one
  another by the probe results alone
- endpoint failures include enough detail for direct user remediation

### Phase 3: User-facing rendering, CLI wiring, and regression tests

Inputs:
- doctor probe/classification results
- `__main__.py` mode validation rules
- existing unit test suites for main and TUI flows

Outputs:
- final text output for `--doctor`
- CLI integration in `main()`
- regression tests covering the core scenarios and exit codes
- validation report with required quality-gate results

Verification:
- output stays concise but actionable in every failure mode
- doctor mode does not regress existing broker/TUI/web-ui entrypoints

## Acceptance Tests

- `pytest tests/unit/test_main.py`
- `pytest tests/unit/test_main_tui.py`
- `pytest tests/unit/test_tui.py`
- `pytest tests/unit/test_doctor.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer a flag-based entrypoint (`--doctor`) to match the current CLI style and
  avoid introducing a separate subcommand parser mid-stream.
- Treat doctor as a shared diagnostics surface, not as a TUI-only helper, so
  later tasks can reuse the same findings in TUI fallback and docs.
- Keep the primary output human-readable first; structured export can remain a
  future enhancement if needed.

## Notes

- Minimize duplication with `tui.py` and current broker-console probes; if local
  status helpers must move into a shared module, do that now instead of growing
  another copy.
- Any new remediation text should align with the recommended dedicated-host
  workflow introduced in `P7-T1`.
- Review subject name for this task: `broker_doctor_diagnostics`.
