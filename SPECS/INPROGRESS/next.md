# Next Task: P6-T1 — Add explicit broker runtime status surface for frontend consumers

**Priority:** P1
**Phase:** Phase 6: Explicit Broker Frontend
**Effort:** 4h
**Dependencies:** none
**Status:** Selected

## Description

Add a structured runtime status surface for the persistent broker so explicit frontends do not need to infer daemon health from pid files and log parsing alone. The surface should expose broker lifecycle state, upstream pid/availability, client session counts, and other operator-facing details that explain whether the daemon is healthy, reconnecting, or awaiting approval.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
