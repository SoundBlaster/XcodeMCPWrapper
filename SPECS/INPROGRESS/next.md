# Next Task: FU-P7-T3-1 — Prioritize foreign port-owner guidance in mixed broker/dashboard conflicts

**Priority:** P1
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 2-3 hours
**Dependencies:** P7-T3
**Status:** Ready

## Description

When startup sees both a live broker PID and a non-broker listener on the
requested dashboard port, current remediation prioritizes broker reset guidance
and can hide the actual foreign port owner. Update startup and diagnostics
conflict ordering so users see the real blocker or one combined recovery path
instead of being sent into a reset loop.

## Recently Archived

- `2026-03-07` — `FU-P7-T1-1` archived with verdict `PASS`
- `2026-03-07` — `P7-T3` archived with verdict `PASS`
- `2026-03-07` — `P7-T2` archived with verdict `PASS`

## Next Step

Create the `FU-P7-T3-1` PRD in `SPECS/INPROGRESS/`, then implement and
validate the mixed-state dashboard conflict guidance updates.
