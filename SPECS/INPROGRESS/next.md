# Next Task: P14-T1 — Bound per-session ID restore maps in broker transport

**Priority:** P1
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Effort:** 1-2h
**Dependencies:** FU-P13-T11 (✅), FU-P13-T15 (✅)
**Status:** Selected

## Description

Prevent unbounded memory growth in long-lived broker sessions by pruning
`id_restore`, `string_id_map`, and `int_id_map` entries after responses are
routed, while preserving ID round-trip fidelity and defining safe wrap behavior
for the local integer ID allocator.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
