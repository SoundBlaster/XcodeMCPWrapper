# Next Task: P7-T1 — Add one-command broker host startup with attached frontend

**Priority:** P0
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 1d
**Dependencies:** P6-T1, P6-T2
**Status:** Selected

## Description

Add a single operator-facing command that starts the dedicated broker host,
ensures the dashboard endpoint is owned by that host, and immediately opens the
terminal frontend against the same runtime. The goal is to remove the current
multi-step manual sequence of starting the daemon, checking the port, and
launching TUI separately.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
