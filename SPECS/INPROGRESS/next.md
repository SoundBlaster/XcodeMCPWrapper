# Next Task: FU-P12-T3-1 — Document unused `error_message` parameter in `MetricsCollector.record_response`

**Priority:** P3
**Phase:** Phase 13: Post-Release Follow-ups
**Effort:** 0.5-1 hour
**Dependencies:** P12-T3
**Status:** Selected

## Description

`MetricsCollector.record_response()` accepts `error_message: Optional[str]` for
API symmetry with `SharedMetricsStore`, but the in-memory collector never
stores or uses it. Add a docstring note clarifying this parameter is accepted
for compatibility and intentionally not persisted.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
