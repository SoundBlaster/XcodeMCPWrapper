# PRD: FU-P13-T14 — Complete interactive Xcode prompt verification and close P13-T5

**Status:** INPROGRESS
**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Dependencies:** P13-T5 (⚠️ PARTIAL), P13-T6 (✅)

---

## 1. Objective

Close the remaining manual-validation gap from P13-T5 by recording concrete prompt
behavior evidence for direct mode and broker mode, then update P13-T5 and BUG-T4
workplan statuses to reflect the final outcome.

---

## 2. Scope

### In scope
- Execute repeatable short-lived session runs in direct mode and broker mode.
- Capture operator-observable evidence for Xcode permission prompt behavior.
- Update archived P13-T5 validation artifacts with PASS/FAIL decision and rationale.
- Reconcile BUG-T4 resolution path with the final P13-T5 outcome.

### Out of scope
- Additional broker runtime implementation changes.
- New client compatibility features.
- UI/dashboard changes.

---

## 3. Validation Design

### 3.1 Session matrix

Use the same test intent in both modes:
- 1 warm-up run.
- 5 repeated short-lived sessions.
- Record whether a permission prompt appears per session.

### 3.2 Evidence policy

Because prompt UI is operator-facing, evidence is documented as:
- Exact commands executed.
- Session timestamps and outcomes.
- Observed prompt count in each mode.
- Supporting automation evidence (existing integration tests and churn metrics).

### 3.3 Decision rules

- **PASS:** direct mode shows repeated prompt churn while broker mode avoids extra
  prompts after initial authorization, or broker mode demonstrates materially fewer
  prompts in the same session matrix.
- **FAIL:** broker mode does not reduce prompt events versus direct mode.
- If evidence is inconclusive, record explicit blocker conditions and create
  follow-up task(s).

---

## 4. Files To Update

| File | Change |
|------|--------|
| `SPECS/ARCHIVE/P13-T5_Validate_prompt_reduction_and_multi_client_stability/P13-T5_manual_prompt_validation.md` | Replace partial result with concrete prompt observations and final decision |
| `SPECS/ARCHIVE/P13-T5_Validate_prompt_reduction_and_multi_client_stability/P13-T5_Validation_Report.md` | Update verdict and acceptance table to PASS/FAIL with evidence |
| `SPECS/Workplan.md` | Mark P13-T5 criterion and BUG-T4 resolution line based on outcome; complete FU-P13-T14 status |
| `SPECS/INPROGRESS/FU-P13-T14_Validation_Report.md` | Record task-level acceptance criteria and quality-gate outcomes |

---

## 5. Acceptance Criteria

- [ ] Interactive desktop run confirms observed prompt behavior for repeated short-lived sessions.
- [ ] P13-T5 manual prompt criterion is resolved to PASS or FAIL with concrete evidence.
- [ ] Any discovered deviations are captured in troubleshooting and/or follow-up bug tasks.
- [ ] BUG-T4 related resolution path is reconciled with the final validation outcome.
- [ ] Quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`) are executed and recorded.

---

## 6. Execution Notes

- Prefer evidence grounded in commands and recorded observations over assumptions.
- Keep archival artifacts append-only in spirit: preserve prior context and clearly
  timestamp FU-P13-T14 updates.

---
**Archived:** 2026-02-19
**Verdict:** FAIL
