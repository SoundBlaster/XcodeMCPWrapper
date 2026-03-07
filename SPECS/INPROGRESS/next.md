# Next Task: P7-T2 — Implement a broker doctor command for cross-black-box diagnostics

**Priority:** P0
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 4-6 hours
**Dependencies:** P6-T1
**Status:** Selected

## Description

Add a `doctor`-style diagnostic command that inspects the full user-visible
chain: Python runtime, local broker files and processes, dashboard endpoint
ownership, and common failure modes such as stale ports, missing dashboard, or
wrong endpoint. The output should help users debug without needing to infer the
internal broker architecture first.

## Next Step

Run the PLAN command to produce the implementation-ready PRD for `P7-T2`.
