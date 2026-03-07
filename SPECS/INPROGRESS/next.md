# Next Task: P7-T2 — Implement a broker doctor command for cross-black-box diagnostics

**Priority:** P0
**Phase:** Phase 7: Broker UX and Diagnostics
**Dependencies:** P6-T1
**Status:** Ready after `P7-T1` CI clears

## Description

Add a `doctor`-style diagnostic command that inspects the full user-visible
chain: Python runtime, local broker files and processes, dashboard endpoint
ownership, and common failure modes such as stale ports, missing dashboard, or
wrong endpoint. The output should help users debug without needing to infer the
internal broker architecture first.

## Recently Archived

- `2026-03-07` — `P7-T1` archived with verdict `PASS`

## Next Step

Wait for the `P7-T1` pull request to clear CI, then run FLOW again to select
and plan `P7-T2`.
