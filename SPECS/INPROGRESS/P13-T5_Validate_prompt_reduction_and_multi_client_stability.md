# PRD: P13-T5 — Validate prompt reduction and multi-client stability

**Status:** IN PROGRESS
**Priority:** P1
**Branch:** `feature/P13-T5-prompt-reduction-multi-client-stability`
**Depends on:** P13-T4 ✅

---

## 1. Overview

P13-T4 introduced broker proxy mode so short-lived MCP client processes can forward through one long-lived broker session. P13-T5 validates that behavior under realistic usage patterns and captures evidence that broker mode reduces upstream bridge churn (and therefore reduces repeated Xcode permission prompts).

This task delivers a reproducible integration test suite, a process-churn comparison report, and a manual validation report that confirms observed prompt behavior while the broker remains running.

---

## 2. Scope

### In-scope
- Add integration tests for sequential and concurrent short-lived proxy clients that share one broker-owned upstream bridge.
- Add assertions/evidence capture for upstream bridge lifecycle stability during client churn.
- Add manual validation report documenting Xcode permission prompt behavior in direct mode vs broker mode.
- Add regression validation commands and results to the task validation report.

### Out-of-scope
- Broker mode documentation rollout/migration guides (P13-T6).
- New broker runtime features unrelated to validation.
- Non-Unix transport behavior.

---

## 3. Design

### 3.1 Test strategy

Create `tests/integration/test_broker_multi_client.py` with targeted scenarios:

1. Sequential short-lived clients:
   - Launch N short-lived proxy client sessions against one broker.
   - Verify all sessions complete successfully.
   - Verify upstream bridge process identity/count stays stable.

2. Concurrent client load:
   - Launch M concurrent client sessions.
   - Verify responses are routed correctly and no cross-talk/corruption occurs.
   - Verify no unexpected broker/upstream restarts during load.

### 3.2 Metrics artifact

Create a metrics artifact in the task archive that compares:
- Direct mode: upstream process starts for N short-lived sessions.
- Broker mode: upstream process starts for N short-lived sessions.

The artifact should include commands/inputs, observed counts, and interpretation.

### 3.3 Manual validation artifact

Create a manual validation report that records:
- Environment (macOS, Python, Xcode version)
- Steps to reproduce for direct mode and broker mode
- Prompt observations for both modes
- Result verdict aligned to acceptance criteria

---

## 4. File changes

| File | Change |
|------|--------|
| `tests/integration/test_broker_multi_client.py` | Add broker multi-client stability integration tests |
| `SPECS/INPROGRESS/P13-T5_Validation_Report.md` | Record quality gate outcomes and acceptance-criteria evidence |
| `SPECS/INPROGRESS/P13-T5_manual_prompt_validation.md` | Manual direct-vs-broker prompt behavior notes |

---

## 5. Acceptance criteria

- [ ] Sequential short-lived clients reuse one broker-owned upstream bridge process
- [ ] Concurrent client tool calls remain stable under load
- [ ] Manual test confirms no extra Xcode prompt while broker stays running
- [ ] Regression suite passes with broker mode enabled

---

## 6. Quality gates

- `pytest` — all tests pass
- `ruff check src/ tests/` — no lint errors
- `mypy src/` — no new type errors
- `pytest --cov` — coverage ≥ 90%
