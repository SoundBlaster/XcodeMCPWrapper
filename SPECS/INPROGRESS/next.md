# Next Task: P7-T4 — Add direct local-status fallback for TUI when dashboard API is unavailable

**Priority:** P1
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 4-5 hours
**Dependencies:** P6-T2
**Status:** Ready

## Description

Reduce TUI dependence on the Web UI API by letting it fall back to local broker
state when the dashboard endpoint is unavailable. The TUI should still provide
useful diagnostics from PID/socket/version files and any directly accessible
broker status sources, while clearly indicating that live dashboard-backed
controls are unavailable.

## Recently Archived

- `2026-03-07` — `FU-P7-T3-2` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-1` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T1-1` archived with verdict `PASS`

## Next Step

Create the `P7-T4` PRD in `SPECS/INPROGRESS/`, then implement and validate the
local broker-status fallback path for TUI.
