# Validation Report: P13-T5 — Validate prompt reduction and multi-client stability

**Date:** 2026-02-19
**Branch:** `feature/P13-T5-prompt-reduction-multi-client-stability`
**Verdict:** FAIL

---

## Quality Gates

| Gate | Result | Details |
|------|--------|---------|
| `pytest` | ✅ PASS | 577 passed, 5 skipped |
| `ruff check src/ tests/` | ✅ PASS | All checks passed |
| `mypy src/` | ✅ PASS | Success: no issues found in 18 source files |
| `pytest --cov` ≥ 90% | ✅ PASS | 92.31% total coverage |

---

## Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Sequential short-lived clients reuse one broker-owned upstream bridge process | ✅ | `tests/integration/test_broker_multi_client.py::test_sequential_short_lived_clients_reuse_single_upstream_bridge` |
| Concurrent client tool calls remain stable under load | ✅ | `tests/integration/test_broker_multi_client.py::test_concurrent_clients_remain_stable_under_load` |
| Manual test confirms no extra Xcode prompt while broker stays running | ❌ FAIL | `SPECS/ARCHIVE/P13-T5_Validate_prompt_reduction_and_multi_client_stability/P13-T5_manual_prompt_validation.md` (2026-02-19 run: broker proxy sessions rejected with `-32003 UID mismatch`) |
| Regression suite passes with broker mode enabled | ✅ | Full `pytest` and `pytest --cov` runs pass |

---

## Artifacts

| File | Description |
|------|-------------|
| `tests/integration/test_broker_multi_client.py` | New integration coverage for sequential reuse, concurrent stability, and single-upstream launch count |
| `SPECS/INPROGRESS/P13-T5_process_churn_metrics.md` | Direct-vs-broker upstream process churn comparison |
| `SPECS/INPROGRESS/P13-T5_manual_prompt_validation.md` | Manual prompt validation procedure and current status |

---

## Notes

- Process churn evidence shows broker mode reduced upstream process starts from 12 to 1 for equivalent short-lived session count in local validation.
- FU-P13-T14 closed the prior partial state by resolving the manual criterion as FAIL with concrete runtime evidence.
- Broker mode currently rejects same-user local clients on this environment (`Errno 42` peer credential check path), blocking prompt-reduction validation until fixed.
- Follow-up remediation is tracked in `FU-P13-T15`.
