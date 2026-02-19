# Next Task: FU-P12-T1-5 — Cap `_clients` dict and prune `client_identities` to prevent unbounded growth

**Priority:** P2
**Phase:** Phase 13: Post-Release Follow-ups
**Effort:** 2-4 hours
**Dependencies:** FU-P12-T1-3
**Status:** Selected

## Description

The in-memory `_clients` dict in `MetricsCollector` and the
`client_identities` SQLite table in `SharedMetricsStore` currently grow without
bound as new `(name, version)` pairs appear. Add a soft cap (target: 50
entries) for `_clients` by evicting the oldest entries using `last_seen`, and
prune stale `client_identities` rows during writes using a `WHERE last_seen > ?`
condition.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
