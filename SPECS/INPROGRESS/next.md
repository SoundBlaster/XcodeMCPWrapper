# Next Task: FU-P12-T1-4 — Make `IN FLIGHT` KPI reflect real in-flight requests in shared-metrics mode

**Priority:** P2
**Phase:** Phase 12: Data Collection Enhancements
**Effort:** 2-4 hours
**Dependencies:** P12-T1
**Status:** Selected

## Description

In shared SQLite metrics mode, `/api/metrics` currently reports `in_flight: 0`
unconditionally. Implement process-safe in-flight tracking so the dashboard's
`IN FLIGHT` KPI shows outstanding requests while they are active and returns to
zero once matching responses arrive.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
