# REBUILD-P10-T1: Spec-Driven Rebuild of Web UI Dashboard

## Summary
Rebuild the existing Web UI feature using the REBUILD workflow (evidence -> spec -> architecture -> phased plan -> compatibility harness) while preserving current observable behavior unless explicitly changed by documented bug fixes.

## Context
- Source feature branch: `feature/p10-t1-web-ui`
- Rebuild branch: `codex/rebuild-p10-t1-web-ui`
- Workflow references:
  - `SPECS/COMMANDS/REBUILD.md`
  - `SPECS/COMMANDS/FLOW.md`

## Scope
- In scope:
  - Produce REBUILD Step 0-7 outputs.
  - Produce final package files in `FEATURE_REBUILD/`.
  - Define architecture and execution workplan for rebuild implementation.
  - Define compatibility and migration strategy.
- Out of scope:
  - Immediate production code refactor for Web UI internals.
  - New dashboard feature additions unrelated to parity or bug fixes.

## Deliverables
1. `FEATURE_REBUILD/STEP-0.json`
2. `FEATURE_REBUILD/STEP-1.json`
3. `FEATURE_REBUILD/STEP-2.json`
4. `FEATURE_REBUILD/STEP-3.json`
5. `FEATURE_REBUILD/STEP-4.json`
6. `FEATURE_REBUILD/STEP-5.json`
7. `FEATURE_REBUILD/STEP-6.json`
8. `FEATURE_REBUILD/STEP-7.json`
9. `FEATURE_REBUILD/ObservedBehavior.md`
10. `FEATURE_REBUILD/Spec.md`
11. `FEATURE_REBUILD/Architecture.md`
12. `FEATURE_REBUILD/Workplan.md`
13. `FEATURE_REBUILD/CompatibilityHarness.md`
14. `FEATURE_REBUILD/Risks.md`

## Acceptance Criteria
- All REBUILD step output files are present and valid JSON.
- `Spec.md` follows required heading structure from Step 3.
- `Architecture.md` follows required heading structure from Step 4.
- `Workplan.md` includes phased task graph with verification commands and rollback plans.
- `CompatibilityHarness.md` defines MUST/MAY parity boundaries and CI integration.
- Package file set matches Step 7 requirements.

## Dependencies
- Existing Web UI implementation and tests in source branch.
- Historical issue evidence and validation artifacts:
  - `SPECS/INPROGRESS/Web_UI_Debugging_Summary.md`
  - `SPECS/ARCHIVE/P10-T2_Fix_Web_UI_Timeseries_Charts/`

## Risks
- Behavior assumptions could drift if evidence is incomplete.
- Historical bug fixes may be accidentally treated as optional instead of baseline compatibility.
- Auth behavior in websocket path may be under-tested.

## Verification Approach
- Validate all step JSON files with `jq`.
- Validate required headings with `rg` checks.
- Sanity-check package contents and cross-file consistency.

## Exit Criteria
Task is complete when all deliverables are created, validated, committed, and archived per FLOW.
