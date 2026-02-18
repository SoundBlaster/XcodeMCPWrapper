# PRD: FU-P13-T4-1 — Fix asyncio.get_event_loop() deprecation in BrokerProxy

**Created:** 2026-02-18
**Priority:** P2
**Branch:** `feature/FU-P13-T4-1-fix-asyncio-loop-deprecation`
**Status:** PLAN

---

## 1. Problem Statement

`src/mcpbridge_wrapper/broker/proxy.py` still uses `asyncio.get_event_loop()` in async code paths. Python 3.10+ deprecates this usage in favor of `asyncio.get_running_loop()` when inside a running event loop.

This follow-up removes deprecated calls in proxy timeout and stdio wrapping helpers without changing broker behavior.

---

## 2. Scope

### In Scope
- Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in:
  - `BrokerProxy._spawn_broker_if_needed`
  - `BrokerProxy._connect_with_timeout`
  - `BrokerProxy._make_stdin_reader`
  - `BrokerProxy._make_stdout_writer`
- Keep semantics unchanged (timeouts, retries, forwarding).
- Run tests and quality gates.

### Out of Scope
- Reconnect behavior changes (`FU-P13-T4-2`).
- Broker daemon lifecycle changes.
- Any CLI/flag behavior changes.

---

## 3. Deliverables

1. `src/mcpbridge_wrapper/broker/proxy.py`
  - Replace all deprecated loop access calls with running-loop access.
  - Cache loop once per method where appropriate.

2. `tests/unit/test_broker_proxy.py` (if needed)
  - Keep/extend tests only if behavior needs explicit coverage updates.

3. `SPECS/INPROGRESS/FU-P13-T4-1_Validation_Report.md`
  - Record command outputs and acceptance evidence.

---

## 4. Acceptance Criteria

- [ ] All `asyncio.get_event_loop()` calls in `src/mcpbridge_wrapper/broker/proxy.py` are replaced with `asyncio.get_running_loop()`.
- [ ] Broker proxy tests pass.
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

- **Risk:** `get_running_loop()` raises `RuntimeError` if called outside a running loop.
  - **Mitigation:** Only use it inside async methods already awaited from running loop contexts.

---

## 7. Validation Plan

1. Verify no `get_event_loop` usages remain in proxy module.
2. Run targeted test module: `pytest tests/unit/test_broker_proxy.py`.
3. Run full required gates and capture results in validation report.
