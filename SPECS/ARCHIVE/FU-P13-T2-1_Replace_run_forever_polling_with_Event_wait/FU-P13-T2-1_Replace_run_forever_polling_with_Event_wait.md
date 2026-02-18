# PRD: FU-P13-T2-1 — Replace run_forever() polling loop with asyncio.Event-based wait

**Created:** 2026-02-18
**Priority:** P3
**Branch:** `codex/feature/FU-P13-T2-1-event-wait-shutdown`
**Status:** PLAN

---

## 1. Problem Statement

`BrokerDaemon.run_forever()` currently waits for shutdown by polling `asyncio.sleep(0.1)`. This adds up to 100ms latency to stop handling and introduces unnecessary wakeups.

---

## 2. Scope

### In Scope
- Replace polling-based wait in `run_forever()` with an `asyncio.Event`-driven wait.
- Preserve startup/shutdown semantics and existing lifecycle behavior.
- Keep current external API and tests intact.

### Out of Scope
- Refactoring broker daemon startup/lock management.
- Changes to proxy or transport behavior.
- New CLI options.

---

## 3. Deliverables

1. `src/mcpbridge_wrapper/broker/daemon.py`
- Introduce event-based shutdown signaling for `run_forever()`.
- Ensure `stop()` triggers the event and remains safe when called multiple times.

2. `tests/unit/test_broker_daemon.py`
- Keep existing behavior checks passing.
- Add or adjust assertions if needed to validate event-wait shutdown behavior.

3. `SPECS/INPROGRESS/FU-P13-T2-1_Validation_Report.md`
- Record quality-gate results and acceptance evidence.

---

## 4. Acceptance Criteria

- [ ] `run_forever()` responds to stop signal within one event loop tick.
- [ ] Existing `test_run_forever_starts_and_stops` passes without behavioral regressions.
- [ ] Full quality gates pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` (coverage >= 90%)

---

## 5. Dependencies

- P13-T2 ✅

---

## 6. Risks and Mitigations

- **Risk:** Event lifecycle may leak across multiple broker runs.
  - **Mitigation:** Reinitialize/reset the event at broker startup boundaries and validate with unit tests.

---

## 7. Validation Plan

1. Implement event-based wait and stop signaling.
2. Run targeted daemon unit tests.
3. Run required quality gates and record outcomes in the validation report.

---
**Archived:** 2026-02-18
**Verdict:** PASS
