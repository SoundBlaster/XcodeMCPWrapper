# FU-P6-T10-1 — Align manual install script with Web UI configuration expectations

**Priority:** P1  
**Dependencies:** P6-T3, P10-T1  
**Phase:** Follow-up Backlog

## Objective
Eliminate the installation mismatch where `scripts/install.sh` installs only base dependencies while users can copy configs that enable `--web-ui`, causing runtime ImportError for missing Web UI packages.

## Deliverables
1. `scripts/install.sh` supports explicit Web UI install mode via `--webui`.
2. `README.md` and `docs/installation.md` clearly map:
   - base install => no `--web-ui` args
   - webui install => `--web-ui` args supported
3. `docs/troubleshooting.md` includes symptom/cause/fix for this mismatch.
4. Validation report records command-level verification.

## Acceptance Criteria
1. `./scripts/install.sh` keeps base install behavior by default.
2. `./scripts/install.sh --webui` installs `-e ".[webui]"` dependencies.
3. `xcodemcpwrapper --web-ui --web-ui-port 8080 --help` does not fail after Web UI install mode.
4. Documentation no longer implies Web UI works on base-only install.

## Execution Plan
1. Extend installer argument parsing and install command selection.
2. Update docs in focused sections only (no broad restructuring).
3. Run quality gates plus targeted runtime checks.
4. Produce `SPECS/INPROGRESS/FU-P6-T10-1_Validation_Report.md`.

---
**Archived:** 2026-02-12
**Verdict:** PASS
