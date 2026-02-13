# FU-P9-T2-2 Validation Report

**Task:** FU-P9-T2-2 — Add troubleshooting guidance for stale uvx cache/process versions  
**Date:** 2026-02-14  
**Verdict:** PASS

## Summary
Implemented troubleshooting and setup documentation updates for stale `uvx` runtime/process scenarios after upgrades, including concrete diagnosis commands, explicit `--refresh` recovery path, and warning about concurrent wrapper processes masking upgrades.

## Deliverables Completed
- Updated `docs/troubleshooting.md` with a dedicated stale-runtime section including:
  - symptom/cause/fix narrative,
  - port/PID/version diagnostics,
  - `uvx --refresh --from 'mcpbridge-wrapper[webui]' ...` recovery,
  - explicit note about multiple concurrent wrapper processes.
- Updated `docs/cursor-setup.md` with a one-time `--refresh` config pattern for post-upgrade recovery.
- Updated `README.md` with runtime process version verification snippet and refresh command.

## Acceptance Criteria Validation
1. Troubleshooting docs include symptom/cause/fix for stale behavior after upgrade.
   - **PASS** — Added section: `"Uptime still shows 1h 0m 0s" or behavior is unchanged after upgrade` in `docs/troubleshooting.md`.
2. Docs include explicit diagnostic commands for port/PID/version validation.
   - **PASS** — Added `lsof`, `ps`, and interpreter-based `importlib.metadata` version checks.
3. Recovery guidance includes `uvx --refresh --from mcpbridge-wrapper[webui] ...` and restart instructions.
   - **PASS** — Added exact command and restart/reload guidance in troubleshooting and Cursor setup docs.
4. Docs clearly mention multiple concurrent wrapper processes can mask upgrades.
   - **PASS** — Added explicit warning in troubleshooting section.
5. Validation report records local repro and confirms refreshed process resolves stale behavior.
   - **PASS** — Local repro captured below with stale vs refreshed runtime evidence.

## Local Reproduction Evidence
```text
stale_pid=8069
stale_version=0.3.2
stale_uptime_samples=3600,3600
refresh_pid=53176
refresh_version=0.3.3
refresh_uptime_samples=0.4,2.4
```

Interpretation:
- Stale listener on port 8080 remained on `0.3.2` and returned fixed uptime.
- Refreshed start used `0.3.3` and returned increasing uptime.

## Quality Gates
- `pytest` — **PASS** (345 passed, 5 skipped)
- `ruff check src/` — **PASS**
- `mypy src/` — **PASS**
- `pytest --cov` — **PASS** (96.62% total, threshold 90%)

## Notes
- Test runs reported non-fatal warnings about occupied local ports (`8080`/`9090`) in background Web UI thread tests; suite still passed and coverage remained above threshold.
