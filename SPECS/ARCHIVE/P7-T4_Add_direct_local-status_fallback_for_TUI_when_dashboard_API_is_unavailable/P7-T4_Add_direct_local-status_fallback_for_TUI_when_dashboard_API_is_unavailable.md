# P7-T4 — Add direct local-status fallback for TUI when dashboard API is unavailable

## Objective Summary

`P6-T2` introduced a terminal frontend for the broker-hosted Web UI, but the
current TUI is still all-or-nothing: if `/api/control` or `/api/broker/status`
cannot be reached, the screen drops to a generic “Broker runtime is
unavailable” message plus raw local file metadata. That leaves users without a
clear answer to the actual question they care about: is the broker still
running locally, are its state files stale, is the dashboard port occupied, or
do they just need to reconnect later after an approval/restart event?

This task should make the TUI useful even when live dashboard-backed data is
down. The fallback does not need to reimplement the full Web UI API. It should
derive the best available local diagnosis from broker PID/socket/version files,
dashboard-port ownership, and any directly accessible local broker state, then
render that diagnosis explicitly as local fallback data. Live dashboard status
and stop control should still be used whenever the API is reachable.

## Deliverables

- Update `src/mcpbridge_wrapper/tui.py` so `BrokerTUIClient.fetch_snapshot()`
  can return a structured local-fallback snapshot when dashboard requests fail.
- Add local fallback diagnostics that distinguish at least:
  running broker without dashboard, foreign listener on the dashboard port,
  stale local runtime files, and no local broker runtime.
- Update the TUI renderer so the screen clearly marks whether broker runtime
  data comes from the live dashboard API or from local fallback state, and
  whether stop control is unavailable in fallback mode.
- Add or extend tests in `tests/unit/test_tui.py` and `tests/unit/test_main_tui.py`
  for fallback diagnosis, rendering, and existing `--tui` CLI behavior.
- Produce `SPECS/INPROGRESS/P7-T4_Validation_Report.md` with targeted and full
  quality-gate evidence.

## Success Criteria

- TUI remains useful when the dashboard API is unavailable and still presents a
  best-effort local broker diagnosis instead of only a generic unreachable
  error.
- The screen explicitly distinguishes live dashboard-backed runtime data from
  local fallback data.
- Users can infer from TUI alone whether they likely need to restart the
  broker, free the dashboard port, clean stale files, or simply attach once the
  dashboard comes back.

## Test-First Plan

1. Add `fetch_snapshot()` tests for unavailable dashboard requests where local
   state indicates:
   a running broker without dashboard,
   a foreign listener on the dashboard port,
   stale broker files,
   and no live broker.
2. Add `render_screen()` tests that assert the UI labels local fallback mode
   distinctly from live dashboard mode and hides stop control as unavailable
   when running on fallback data.
3. Keep existing live-dashboard tests intact so fallback logic does not regress
   healthy TUI behavior or stop control handling.
4. Implement the smallest production change needed to populate structured local
   fallback fields and render them clearly.
5. Run required quality gates: `pytest`, `ruff check src/`, `mypy src/`, and
   `pytest --cov`.

## Execution Plan

### Phase 1: Define fallback snapshot and screen contract

Inputs:
- `src/mcpbridge_wrapper/tui.py`
- existing `BrokerTUISnapshot` rendering path
- current TUI tests in `tests/unit/test_tui.py`

Outputs:
- failing tests that pin fallback-mode labels and diagnosis text
- a clear screen contract for live data vs local fallback data

Verification:
- fallback tests fail against the current “runtime unavailable” behavior
- existing healthy-runtime rendering expectations remain unchanged

### Phase 2: Add local diagnosis collection

Inputs:
- local broker files (`broker.pid`, `broker.sock`, `broker.version`)
- configured dashboard port derived from `runtime.base_url`
- any reusable local listener/process helpers already in the repo

Outputs:
- local fallback classification that can tell apart:
  broker running without dashboard,
  foreign listener conflict,
  stale runtime files,
  and broker-not-running states
- fallback snapshot fields suitable for pure rendering tests

Verification:
- unavailable dashboard path returns structured fallback data instead of only
  an opaque error string
- foreign dashboard-port listeners remain visible in fallback mode

### Phase 3: Render and validate fallback mode

Inputs:
- fallback snapshot data
- `render_screen()` and `BrokerTUI` loop behavior
- full repository quality gates

Outputs:
- TUI screen that clearly identifies fallback mode, shows the local diagnosis,
  and marks live dashboard controls as unavailable when appropriate
- validation report with targeted tests and full gate results

Verification:
- the screen communicates both the diagnosis and the reduced capability surface
- coverage remains at or above the repository threshold

## Acceptance Tests

- `pytest tests/unit/test_tui.py`
- `pytest tests/unit/test_main_tui.py`
- `pytest`
- `ruff check src/`
- `mypy src/`
- `pytest --cov`

## Decision Points

- Prefer a lightweight local diagnosis helper inside the TUI path or a shared
  helper reused from existing diagnostics code, but avoid duplicating large
  chunks of doctor rendering logic in the curses UI.
- Fallback mode should remain read-only for broker runtime data; if the
  dashboard API is unavailable, stop control should be shown as unavailable even
  if local files suggest the broker is running.
- The screen should preserve the current live dashboard view when HTTP succeeds,
  and only switch to local fallback when the dashboard API is unavailable.

## Notes

- No documentation changes are expected unless the visible TUI command/help
  text changes.
- Review subject name for this task: `tui_local_status_fallback`.
