# Next Task: FU-P7-T3-2 — Exclude broker-owned dashboard listeners from foreign port-conflict guidance

**Priority:** P1
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 2-3 hours
**Dependencies:** FU-P7-T3-1
**Status:** Selected

## Description

Refine the mixed broker/dashboard conflict classifier so it distinguishes the
broker daemon's own dashboard listener from a foreign process on the same port.
When degraded probes occur against a broker-owned listener, startup and
diagnostics should keep users on broker-health guidance instead of reporting a
foreign port owner.

## Recently Archived

- `2026-03-07` — `FU-P7-T3-1` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T1-1` archived with verdict `PASS`
- `2026-03-07` — `P7-T3` archived with verdict `PASS`

## Next Step

Create the `FU-P7-T3-2` PRD in `SPECS/INPROGRESS/`, then implement and validate
the broker-owned-listener exclusion in startup and doctor mixed-state guidance.
