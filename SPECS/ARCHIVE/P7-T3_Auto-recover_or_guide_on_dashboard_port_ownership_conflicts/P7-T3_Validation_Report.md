# P7-T3 Validation Report

**Task:** P7-T3 — Auto-recover or guide on dashboard port ownership conflicts
**Date:** 2026-03-07
**Verdict:** PASS

## Summary

Implemented the broker-hosted dashboard conflict fix by:

- removing the silent broker-daemon partial state where `--broker-daemon --web-ui`
  could continue without the requested dashboard
- adding shared user-facing remediation helpers in
  `src/mcpbridge_wrapper/__main__.py` so startup now resolves occupied-port
  states into explicit attach, reset, or restart-assisted guidance
- aligning `--broker-console` conflict messaging with the dedicated-host
  workflow already surfaced by `--doctor`
- preserving the safe recovery path via
  `mcpbridge-wrapper --broker-console --web-ui-restart`
- extending unit coverage for foreign listeners, running brokers without a
  dashboard, already-healthy broker-backed endpoints, and restart-assisted
  recovery
- refreshing published coverage references in `README.md`,
  `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`, and
  `AGENTS.md` to the validated current total

## Files Validated

- `src/mcpbridge_wrapper/__main__.py`
- `tests/unit/test_main.py`
- `tests/unit/test_doctor.py`
- `README.md`
- `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md`
- `AGENTS.md`

## Targeted Verification

```bash
pytest tests/unit/test_main.py tests/unit/test_main_tui.py tests/unit/test_doctor.py tests/unit/test_tui.py
```

- Result: `163 passed`

```bash
pytest tests/unit/test_main.py -k 'broker_console or broker_daemon_webui_port_occupied or broker_lacks_dashboard'
```

- Result: `18 passed`

```bash
python scripts/check_doc_sync.py --all --require-same-commit
```

- Result: `PASS`
- Observed outcome: README and DocC coverage references remained in sync after
  updating the validated coverage metric

## Required Quality Gates

```bash
pytest
```

- Result: `887 passed, 5 skipped in 7.98s`

```bash
python -m ruff check src/ tests/
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

- Result: `887 passed, 5 skipped in 8.97s`
- Coverage: `91.62%`

## Notes

- The new startup contract is intentionally fail-fast for explicit `--web-ui`
  requests. A running broker without the requested frontend is now treated as a
  broken state, not a successful launch.
- Doctor messaging already matched the intended dedicated-host recovery path, so
  this task focused on aligning startup/orchestration behavior to that model
  instead of inventing a separate recovery surface.
- Remaining warnings are the pre-existing `websockets` / `uvicorn`
  deprecations already visible in the repository test suite.
