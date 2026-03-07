# Next Task: P7-T3 — Auto-recover or guide on dashboard port ownership conflicts

**Priority:** P0
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 4-6 hours
**Dependencies:** P6-T1, P7-T2
**Status:** Ready after `P7-T2` CI clears

## Description

Improve the broker-hosted dashboard startup path so users do not get stranded
when the desired Web UI port is occupied by a stale or unrelated process.
Prefer deterministic recovery or one explicit remediation path over the current
partial state where the broker can stay alive without the dashboard/frontend
required by the recommended UX flow.

## Recently Archived

- `2026-03-07` — `P7-T2` archived with verdict `PASS`

## Next Step

Wait for the `P7-T2` pull request to clear CI, then run FLOW again to select
and plan `P7-T3`.
