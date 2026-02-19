# Next Task: FU-P13-T13-FU-1 — Set _stopped_event and _stop_event in _rollback_startup for defensive consistency

**Priority:** P3
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Effort:** 30-60m
**Dependencies:** FU-P13-T13 (✅)
**Status:** Selected

## Description

After `_rollback_startup()` sets broker state to `STOPPED`, also set
`self._stopped_event` and `self._stop_event` so event flags are consistent with
the STOPPED contract in future call paths.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
