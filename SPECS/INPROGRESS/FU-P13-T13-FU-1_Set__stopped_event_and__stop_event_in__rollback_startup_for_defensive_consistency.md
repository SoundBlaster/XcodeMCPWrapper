# PRD: FU-P13-T13-FU-1 — Set _stopped_event and _stop_event in _rollback_startup for defensive consistency

**Status:** INPROGRESS
**Priority:** P3
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Dependencies:** FU-P13-T13 (✅)

---

## 1. Objective

Ensure `_rollback_startup()` leaves event flags fully consistent with STOPPED
state by setting both `_stop_event` and `_stopped_event` during rollback.

---

## 2. Background

`_rollback_startup()` currently:
- Cancels read task
- Terminates upstream
- Cleans files
- Sets `self._state = BrokerState.STOPPED`

It does not explicitly set `_stop_event` / `_stopped_event` in this path. While
current call paths do not await these events after startup rollback, setting them
is a defensive consistency improvement and prevents future state/event mismatch.

---

## 3. Design

1. Update `BrokerDaemon._rollback_startup()` to call:
   - `self._stop_event.set()`
   - `self._stopped_event.set()`
2. Keep existing rollback sequence and error behavior unchanged.
3. Add regression test asserting both events are set after a startup failure
   that triggers rollback.

---

## 4. Files To Change

| File | Change |
|------|--------|
| `src/mcpbridge_wrapper/broker/daemon.py` | Set stop/stopped events in `_rollback_startup()` |
| `tests/unit/test_broker_daemon.py` | Add assertion coverage for event state after rollback |
| `SPECS/INPROGRESS/FU-P13-T13-FU-1_Validation_Report.md` | Record validation and quality-gate outcomes |

---

## 5. Acceptance Criteria

- [ ] `_stopped_event.set()` called in `_rollback_startup()`
- [ ] `_stop_event.set()` called in `_rollback_startup()`
- [ ] Tests verify event states are set after a failed startup
- [ ] Quality gates are executed and recorded
