# Next Task: P7-T4 — Add direct local-status fallback for TUI when dashboard API is unavailable

**Priority:** P1
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 4-5 hours
**Dependencies:** P6-T2
**Status:** Ready

## Description

Reduce TUI dependence on the dashboard HTTP API by letting it fall back to the
best available local broker state when the dashboard endpoint is unavailable.
Users should still be able to tell whether the broker is alive, whether the
frontend/control plane is degraded, and which restart/recovery step to take
next without leaving the TUI.

## Recently Archived

- `2026-03-07` — `P7-T3` archived with verdict `PASS`
- `2026-03-07` — `P7-T2` archived with verdict `PASS`

## Next Step

Create the `P7-T4` PRD in `SPECS/INPROGRESS/`, then implement and validate the
local broker-status fallback path for TUI.
