# Validation Report: FU-P13-T14 — Complete interactive Xcode prompt verification and close P13-T5

**Date:** 2026-02-19
**Verdict:** FAIL

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Interactive desktop run confirms observed prompt behavior for repeated short-lived sessions | ✅ PASS (direct mode completed; broker mode exercised and captured with concrete runtime outcomes) |
| 2 | P13-T5 manual prompt criterion is resolved to PASS or FAIL with concrete evidence | ✅ PASS (resolved to **FAIL**) |
| 3 | Any discovered deviations are captured in troubleshooting and/or follow-up bug tasks | ✅ PASS (`FU-P13-T15` added) |
| 4 | BUG-T4 related resolution path is reconciled with the final validation outcome | ✅ PASS (Workplan BUG-T4 path updated) |
| 5 | Quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`) are executed and recorded | ✅ PASS |

---

## Prompt Verification Evidence

### Direct mode (1 warm-up + 5 sessions)

Command shape:

```bash
python -m mcpbridge_wrapper
```

Observed outcome:
- All sessions returned initialize success responses (`id: 1`) in ~0.08s–0.11s.

### Broker mode (1 warm-up + 5 sessions)

Command shape:

```bash
python -m mcpbridge_wrapper --broker-connect
```

Observed outcome:
- All sessions returned JSON-RPC error:
  - `{"code":-32003,"message":"Forbidden: UID mismatch"}`
- Broker daemon stderr repeatedly reported:
  - `Cannot verify peer UID ... [Errno 42] Protocol not available — rejecting connection.`

Interpretation:
- Broker-mode flows are blocked before tool execution, so P13-T5 prompt criterion cannot pass.
- This closes the previously partial P13-T5 criterion with a concrete **FAIL** verdict.

---

## Quality Gates

| Gate | Result | Notes |
|------|--------|-------|
| `pytest` | ❌ FAIL | 5 failures total; broker auth rejections in `tests/integration/test_broker_multi_client.py` plus 2 pre-existing environment-sensitive failures (`test_broker_stubs.py`, `test_broker_transport.py`). |
| `ruff check src/` | ✅ PASS | All checks passed. |
| `mypy src/` | ✅ PASS | Success: no issues found in 18 source files. |
| `pytest --cov` | ❌ FAIL | Same 5 failures as above; coverage still 92.09% (>=90%). |

---

## Follow-up

- Added `FU-P13-T15` to track broker peer-credential fallback/compatibility fix so same-user local connections work on environments where current peer-UID path returns `Errno 42`.
