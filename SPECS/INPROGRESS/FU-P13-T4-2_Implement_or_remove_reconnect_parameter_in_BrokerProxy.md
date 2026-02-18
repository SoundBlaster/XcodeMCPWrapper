# PRD: FU-P13-T4-2 — Implement or remove reconnect parameter in BrokerProxy

**Created:** 2026-02-18
**Priority:** P2
**Branch:** `codex/feature/FU-P13-T4-2-reconnect-parameter`
**Status:** PLAN

---

## 1. Problem Statement

`BrokerProxy` accepts a `reconnect` parameter, stores it, and documents reconnect behavior, but `_run_bridge` never reads this setting. This leaves dead configuration in the API and ambiguous expectations for callers.

---

## 2. Scope

### In Scope
- Remove the unused `reconnect` parameter from `BrokerProxy.__init__` and internal state.
- Remove reconnect claims from proxy module docs/docstrings that no longer match behavior.
- Update call sites and tests that pass `reconnect=`.
- Add/adjust tests to ensure no dead reconnect API remains.

### Out of Scope
- Adding reconnect loop behavior to proxy I/O lifecycle.
- Broker daemon reconnect logic (`broker/daemon.py`).
- New CLI flags for reconnect tuning.

---

## 3. Deliverables

1. `src/mcpbridge_wrapper/broker/proxy.py`
- Remove `reconnect` constructor argument and `_reconnect` field.
- Update docstrings to reflect current behavior (no proxy-level reconnect retry).

2. `src/mcpbridge_wrapper/__main__.py`
- Remove obsolete `reconnect=False` argument at proxy construction.

3. `tests/unit/test_broker_proxy.py`
- Keep coverage around proxy forwarding/connect/exit behavior and ensure API remains clean.

4. `SPECS/INPROGRESS/FU-P13-T4-2_Validation_Report.md`
- Record quality-gate results and acceptance evidence.

---

## 4. Acceptance Criteria

- [ ] `BrokerProxy.__init__` no longer exposes an unused `reconnect` parameter.
- [ ] No dead reconnect state remains in proxy implementation.
- [ ] Relevant unit tests pass with updated API.
- [ ] Full quality gates pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov` (coverage >= 90%)

---

## 5. Dependencies

- P13-T4 ✅

---

## 6. Risks and Mitigations

- **Risk:** Existing callers may still pass `reconnect=` and break at runtime.
  - **Mitigation:** Update known call site (`__main__.py`) and run full test suite to catch hidden usage.

---

## 7. Validation Plan

1. Search repository for `reconnect=` uses in proxy construction and remove obsolete usage.
2. Run `pytest tests/unit/test_broker_proxy.py`.
3. Run required quality gates and record outputs in validation report.

