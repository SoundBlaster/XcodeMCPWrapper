## REVIEW REPORT — tui_local_status_fallback

**Scope:** origin/main..HEAD (P7-T4 commits)
**Files:** 2 (`src/mcpbridge_wrapper/tui.py`, `tests/unit/test_tui.py`)

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `_build_local_fallback_broker` does not expose `upstream_pid`, `connected_clients`, or other rich fields**
The fallback broker dict only exposes `state`, `pid`, `socket_path`, and `version`. The render path renders several fields (`upstream_pid`, `connected_clients`, `upstream_alive`, etc.) that will show as `n/a` in fallback mode. This is by design per the PRD ("bounded local-only broker view"), but an inline comment or docstring note would clarify this intentional limitation to future readers.
_Suggestion:_ Add a brief comment to `_build_local_fallback_broker` noting that fields not derivable from local files are intentionally omitted.

**[Low] `service_name` uses raw string `"local-fallback"` as a status value**
`BrokerTUISnapshot.service_name` is re-used as both a display label and a status sentinel (`"local-fallback"`). This dual purpose is subtle; the render path uses it only for display and doesn't branch on it, so there is no practical bug, but it couples unrelated concerns.
_Suggestion:_ Acceptable as-is for now; could be separated in a future refactor.

**[Nit] `test_fetch_snapshot_surfaces_runtime_errors` previously only asserted `available is False`**
The test was strengthened as part of this task (now also asserts `broker is None` and `runtime_source == "dashboard-unavailable"`), which is good. The original assertion was undershooting — this is a positive improvement.

---

### Architectural Notes

- The fallback is correctly read-only: `can_stop=False` is always set when the dashboard is unavailable, and `request_stop()` is never called from the TUI loop in fallback mode. This preserves the invariant that broker control only flows through the authenticated Web UI API.
- `_read_local_pid` + `_read_local_version` are pure helpers with no side effects, making them easy to test and reuse if a future doctor integration needs them.
- The three-tier `runtime_source` taxonomy (`"dashboard-api"`, `"local-fallback"`, `"dashboard-unavailable"`) is clean and stable. The render label mapping in `_runtime_source_label` ensures the user never sees the raw internal token.
- `render_screen` condition changed from `if snapshot.available and broker` to `if broker` — this is the correct gate for fallback mode, since `available` is always `False` when the dashboard is down but local data exists. The old condition was silently suppressing useful fallback output.

---

### Tests

- 38 TUI tests pass (5 new tests covering fallback paths).
- New tests are well-isolated using `patch` for `_read_local_pid`, `_read_local_version`, and `tail_log_lines`.
- `test_run_loop_does_not_call_stop_without_live_control` is a particularly valuable regression guard.
- Coverage: `tui.py` 96.1%, total 91.75% — above the 90% threshold.
- Uncovered lines in `tui.py` (470, 509–510) relate to `_display_value` edge path and `_read_local_pid` PermissionError branch — acceptable misses given the mock-based test strategy.

---

### Next Steps

- No blockers. Low/nit findings do not warrant follow-up tasks.
- FOLLOW-UP: **skipped** — no actionable issues.
- Proceed to ARCHIVE-REVIEW → PR → CI-REVIEW.
