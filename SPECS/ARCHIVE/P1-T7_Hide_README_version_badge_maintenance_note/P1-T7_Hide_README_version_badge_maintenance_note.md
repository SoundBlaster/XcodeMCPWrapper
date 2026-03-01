# PRD — P1-T7: Hide README version badge maintenance note

## Context

The README currently includes an internal maintenance instruction line:
`Version badge maintenance: run make badge-version (or make badge-version-check in CI).`

This task hides that line from public README content while keeping the version badge itself visible and unchanged.

## Scope

- In scope:
  - Remove the maintenance note line from `README.md`.
  - Preserve surrounding badges and README rendering.
- Out of scope:
  - Changing badge URL, version value, or badge automation scripts.
  - Any code/runtime behavior changes.

## Deliverables

1. `README.md` updated to remove the maintenance note string.
2. Validation report documenting checks performed.

## Acceptance Criteria

- [ ] `README.md` no longer contains the exact string:
      `Version badge maintenance: run make badge-version (or make badge-version-check in CI).`
- [ ] Version badge remains visible in the badges area.
- [ ] No unintended README formatting regressions are introduced.

## Validation Plan

- Run `rg -n "Version badge maintenance" README.md` and confirm no matches.
- Inspect top README section (`nl -ba README.md | sed -n '1,30p'`) to confirm badge block remains present.

## Risks and Mitigations

- Risk: Removing the line could collapse spacing around the badge block.
  - Mitigation: Manually inspect the first 30 lines of `README.md` after change.
