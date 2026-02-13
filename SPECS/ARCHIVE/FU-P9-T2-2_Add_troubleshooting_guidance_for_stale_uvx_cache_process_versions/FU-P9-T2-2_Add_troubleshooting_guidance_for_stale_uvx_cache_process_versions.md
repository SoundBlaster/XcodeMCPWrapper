# FU-P9-T2-2 — Add troubleshooting guidance for stale uvx cache/process versions

**Priority:** P1  
**Dependencies:** P9-T2, FU-P9-T2-1  
**Phase:** Phase 9 Follow-up Backlog

## Objective
Document and validate the stale-runtime failure mode where users still run an older `uvx` environment/process after a release, resulting in unchanged behavior (for example uptime stuck at `1h 0m 0s`) even though updated packages exist.

## Deliverables
1. Add a dedicated troubleshooting section in `docs/troubleshooting.md` for stale `uvx` cache/process diagnosis.
2. Add a recovery note in `docs/cursor-setup.md` explaining one-time use of `--refresh` after releases and restart behavior.
3. Add a quick runtime-version verification snippet in `README.md` for Web UI users.
4. Include concrete commands to:
   - identify process listening on Web UI port,
   - inspect active runtime package version for that process,
   - restart with `uvx --refresh --from mcpbridge-wrapper[webui] ...`.
5. Produce validation evidence in `SPECS/INPROGRESS/FU-P9-T2-2_Validation_Report.md`.

## Acceptance Criteria
1. Troubleshooting docs include symptom/cause/fix for stale behavior after upgrade.
2. Docs include explicit diagnostic commands for port/PID/version validation.
3. Recovery guidance includes `uvx --refresh --from mcpbridge-wrapper[webui] ...` and restart instructions.
4. Docs clearly mention multiple concurrent wrapper processes can mask upgrades.
5. Validation report records local repro and confirms refreshed process resolves stale behavior.

## Execution Plan
1. Update `docs/troubleshooting.md` with symptom, root cause, diagnosis workflow, and recovery flow.
2. Update `docs/cursor-setup.md` with post-upgrade refresh guidance for `uvx` + Web UI usage.
3. Update `README.md` with a concise runtime-version verification snippet.
4. Run required quality gates per FLOW:
   - `pytest`
   - `ruff check src/`
   - `mypy src/`
   - `pytest --cov` (>= 90%)
5. Capture outcomes and acceptance mapping in validation report.

---
**Archived:** 2026-02-13
**Verdict:** PASS
