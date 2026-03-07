# P7-T2 Validation Report

**Task:** P7-T2 — Implement a broker doctor command for cross-black-box diagnostics
**Date:** 2026-03-07
**Verdict:** PASS

## Summary

Implemented a user-facing broker diagnostics command by:

- adding `--doctor` as a dedicated CLI mode in
  `src/mcpbridge_wrapper/__main__.py`
- introducing `src/mcpbridge_wrapper/doctor.py` to collect and classify Python
  runtime identity, local broker files/processes, dashboard ownership, and
  broker-backed runtime state
- distinguishing actionable diagnosis buckets such as healthy runtime,
  version mismatch, stale local state, broker without dashboard, wrong
  dashboard service, occupied dashboard port, and degraded broker-backed state
- rendering one concise user-facing report with summary, next action, and
  supporting evidence instead of requiring manual `lsof` / `curl` debugging
- adding focused unit coverage for helper probes, classification branches,
  CLI wiring, and output rendering

## Files Validated

- `src/mcpbridge_wrapper/__main__.py`
- `src/mcpbridge_wrapper/doctor.py`
- `tests/unit/test_doctor.py`
- `tests/unit/test_main_doctor.py`

## Targeted Verification

```bash
pytest tests/unit/test_doctor.py tests/unit/test_main_doctor.py
```

- Result: `30 passed`

```bash
pytest tests/unit/test_doctor.py tests/unit/test_main_doctor.py --cov=mcpbridge_wrapper.doctor --cov-report=term-missing --no-cov-on-fail
```

- Result: `30 passed`
- Doctor module coverage: `90.68%`

```bash
python -m mcpbridge_wrapper --doctor
```

- Result: command executed successfully in the local dedicated-host setup
- Observed summary: `Status: OK`
- Observed diagnosis: broker daemon and broker-backed dashboard were reported healthy

## Required Quality Gates

```bash
pytest
```

- Result: `884 passed, 5 skipped in 7.98s`

```bash
ruff check src/ tests/
```

- Result: `All checks passed!`

```bash
mypy src/
```

- Result: `Success: no issues found in 20 source files`

```bash
make format-check
```

- Result: `55 files already formatted`

```bash
pytest --cov=src --cov-report=term
```

- Result: `884 passed, 5 skipped in 8.90s`
- Coverage: `91.72%`

## Notes

- The new doctor output is human-readable first and optimized for the
  dedicated-host broker workflow introduced in `P7-T1`.
- The CLI smoke test used the current local runtime and confirmed that doctor
  can identify a healthy broker-backed dashboard without requiring extra flags.
- Remaining warnings are the pre-existing `websockets` / `uvicorn`
  deprecations already seen in the repository test suite.
