# Next Task: FU-P12-T1-6 — Uniform HTML escaping in `renderClientWidgets`

**Priority:** P3
**Phase:** Phase 13: Post-Release Follow-ups
**Effort:** 1-2 hours
**Dependencies:** FU-P12-T1-3
**Status:** Selected

## Description

In `dashboard.js`, `renderClientWidgets` currently interpolates `count` and
`lastSeen` values directly into `innerHTML` while `name` and `version` are
escaped. Apply `escapeHtml()` uniformly to all interpolated widget values to
keep rendering behavior and security posture consistent.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
