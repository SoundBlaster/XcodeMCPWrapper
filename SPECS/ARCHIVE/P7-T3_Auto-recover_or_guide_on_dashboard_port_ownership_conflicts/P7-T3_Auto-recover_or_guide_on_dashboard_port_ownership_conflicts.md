# P7-T3 — Auto-recover or guide on dashboard port ownership conflicts

## Objective Summary

`P7-T1` introduced the explicit dedicated-host workflow and `P7-T2` gave users
one-command diagnostics, but the most confusing failure mode is still in the
startup path itself: `--broker-daemon --web-ui` can leave a running broker
behind while silently skipping the dashboard whenever the desired port is
occupied. That produces a partial state where the recommended frontend is down,
TUI cannot attach, and the user is forced to reason about multiple black boxes
at once.

`P7-T3` should remove that ambiguity. When users request the broker-hosted
dashboard, startup must either recover deterministically into a usable state or
stop with one explicit remediation path. The implementation should align
broker-daemon startup, broker-console orchestration, doctor messaging, and TUI
feedback around the same model so the user is never told that a degraded
dashboard-less host is “good enough”.

## Deliverables

- Tighten the broker-daemon startup path in
  `src/mcpbridge_wrapper/__main__.py` so an explicit `--web-ui` request does not
  silently degrade into “broker without dashboard”.
- Add shared logic that classifies dashboard port conflicts into actionable
  buckets:
  - healthy broker-backed dashboard already serving the port
  - foreign or stale listener on the desired port
  - local broker already running without dashboard on the desired port
  - restart-eligible wrapper-owned listener when `--web-ui-restart` is used
- Update user-facing messaging so the failing command prints one clear next
  action instead of continuing in a partial state.
- Extend doctor/TUI-facing guidance where needed so conflict explanations and
  remediation text stay consistent with the startup behavior.
- Add regression tests for broker-daemon, broker-console, and diagnostics
  scenarios that previously stranded users.

## Success Criteria

- `mcpbridge-wrapper --broker-daemon --web-ui` no longer leaves a healthy-seeming
  broker running without the requested dashboard when the port cannot be used.
- Port conflicts resolve into one of two outcomes only:
  - the requested broker-backed dashboard becomes available, or
  - the command exits non-zero with an explicit remediation path
- `--broker-console` and `--doctor` surface the same conflict class and
  recommended next action for the same runtime state.
- Tests pin both safe recovery and fail-fast behavior so future changes do not
  reintroduce the hidden partial state.

## Test-First Plan

1. Add broker-daemon CLI tests that lock in the new fail-fast behavior when
   `--web-ui` is requested but the target port is occupied by a foreign
   listener, stale listener, or unusable existing runtime.
2. Add orchestration tests for `--broker-console` that verify it reuses a
   healthy broker-backed dashboard, restarts only when explicitly permitted, and
   reports a single remediation path for foreign ownership conflicts.
3. Add doctor classification/rendering tests for the updated conflict buckets so
   diagnostics remain aligned with the startup behavior.
4. Only after the new expectations are pinned, implement the shared conflict
   classifier and wire it into the daemon startup/orchestration flow.
5. Run required quality gates: `pytest`, `ruff check src/`, `mypy src/`, and
   `pytest --cov`.

## Execution Plan

### Phase 1: Define the startup contract

Inputs:
- `src/mcpbridge_wrapper/__main__.py`
- existing broker-console/dashboard probe helpers
- `src/mcpbridge_wrapper/doctor.py`

Outputs:
- a clear contract for what counts as “dashboard ready”
- shared conflict categories for healthy reuse, recoverable ownership, and
  explicit remediation
- deterministic stderr wording for broker-daemon and broker-console entrypoints

Verification:
- every dashboard startup branch ends in either usable dashboard availability or
  non-zero failure
- no code path continues with `--web-ui` requested after a port conflict unless
  the dashboard is actually reachable

### Phase 2: Implement shared conflict handling

Inputs:
- dashboard port probes and listener ownership helpers
- broker PID/socket/version state
- existing `/api/control` and `/api/broker/status` probes

Outputs:
- reusable conflict-resolution helper(s) for broker startup/orchestration
- explicit reuse path for already-healthy broker-backed dashboards
- fail-fast or restart-assisted path for foreign/stale ownership conflicts

Verification:
- running broker + healthy dashboard remains a no-op/reuse case
- foreign listeners and broker-without-dashboard states do not continue as
  “success”

### Phase 3: Align diagnostics and finalize validation

Inputs:
- shared conflict results from startup/orchestration
- doctor and TUI user guidance
- unit and integration tests covering startup/diagnostic flows

Outputs:
- aligned doctor guidance for port ownership conflicts
- regression tests across broker-daemon, broker-console, and doctor
- validation report with required quality-gate output

Verification:
- the same runtime state yields the same diagnosis and remediation whether users
  encounter it during startup, in TUI, or via `--doctor`
- no existing broker/web-ui/TUI entrypoints regress

## Acceptance Tests

- `pytest tests/unit/test_main.py`
- `pytest tests/unit/test_main_tui.py`
- `pytest tests/unit/test_doctor.py`
- `pytest tests/unit/test_tui.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer fail-fast over silent degradation for explicit `--web-ui` requests; a
  running broker without the requested dashboard is a broken UX state, not a
  successful startup.
- Reuse the existing dashboard probe surfaces instead of inventing a second
  ownership model just for startup recovery.
- Keep automatic recovery narrowly scoped to deterministic wrapper-owned cases;
  otherwise print one clear remediation path and exit.

## Notes

- If implementation exposes common conflict helpers that both `doctor.py` and
  `__main__.py` should consume, prefer that refactor now over duplicating
  ownership logic again.
- The dedicated-host workflow introduced in `P7-T1` remains the product path;
  messaging should continue to steer users toward `--broker-console` or
  `--broker-daemon --web-ui`, not ad-hoc manual recovery.
- Review subject name for this task: `dashboard_port_ownership_conflicts`.

---
**Archived:** 2026-03-07
**Verdict:** PASS
