# P1-T2 PRD — Add Xcode 26.4 known issue release-notes link to README

## Objective

Update `README.md` so users have an explicit, authoritative reference to Apple’s official Xcode 26.4 release notes entry for the Coding Intelligence known issue where repeated "Allow Connection?" dialogs can appear with external development tools. The change should improve troubleshooting clarity without introducing speculative guidance, and keep the README aligned with official wording and issue ID `170721057`.

## Scope and Deliverables

- Add a short known-issue note to `README.md` in an appropriate troubleshooting or setup section.
- Include a direct link to Apple’s official Xcode 26.4 release notes page:
  - `https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes`
- Reference the issue context and identifier:
  - "Coding Intelligence" known issue
  - repeated "Allow Connection?" dialogs
  - issue ID `170721057`
- Produce `SPECS/INPROGRESS/P1-T2_Validation_Report.md` with command evidence and acceptance checks.

## Success Criteria and Acceptance Tests

- `README.md` includes the official Xcode 26.4 release-notes URL.
- `README.md` explicitly mentions the known issue text context and issue ID `170721057`.
- Documentation style remains consistent with existing README tone and formatting.
- Required quality gates run and pass for this task branch:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` (coverage remains >= 90%).

## Test-First Plan

1. Identify the most appropriate existing README section before editing to minimize structural churn.
2. Add/adjust documentation text in a single focused README edit.
3. Verify link and issue reference presence with targeted grep checks before running full quality gates.

## Execution Plan

### Phase 1: Documentation placement and wording

- Inputs: current `README.md` structure and troubleshooting/setup sections.
- Outputs: concise known-issue note draft with Apple link and issue ID.
- Verification: local read-through confirms wording is specific and non-duplicative.

### Phase 2: README implementation

- Inputs: approved note content from Phase 1.
- Outputs: updated `README.md` section containing the official link and issue note.
- Verification: `rg` checks confirm URL and `170721057` appear exactly as intended.

### Phase 3: Validation and reporting

- Inputs: updated docs and repository quality-gate commands.
- Outputs: `SPECS/INPROGRESS/P1-T2_Validation_Report.md` with command results and acceptance checklist.
- Verification: all required gates pass and coverage remains at/above project threshold.

## Decision Notes and Constraints

- Keep this task documentation-only; no behavior changes to runtime code.
- Use official Apple terminology and avoid unsupported mitigation claims.
- If related wording already exists, prefer refining existing text over adding redundant sections.

## Notes (Post-Implementation)

- Archive artifacts must include this PRD and validation report.
- REVIEW subject for this task: `p1_t2_xcode_26_4_known_issue_link`.

---
**Archived:** 2026-02-28
**Verdict:** PASS
