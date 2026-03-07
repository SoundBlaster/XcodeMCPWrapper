# Next Task: P7-T3 — Auto-recover or guide on dashboard port ownership conflicts

**Priority:** P0
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 4-6 hours
**Dependencies:** P6-T1, P7-T2
**Status:** Selected

## Description

Improve the broker-hosted dashboard startup path so users do not get stranded
when the desired Web UI port is occupied by a stale or unrelated process.
Prefer deterministic recovery or one explicit remediation path over the current
partial state where the broker can stay alive without the dashboard/frontend
required by the recommended UX flow.

## Recently Archived

- `2026-03-07` — `P7-T2` archived with verdict `PASS`

## Next Step

Create the `P7-T3` PRD in `SPECS/INPROGRESS/`, then implement and validate the
dashboard port-conflict recovery path.
