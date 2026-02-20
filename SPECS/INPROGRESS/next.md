# Next Task: P14-T5 — Stabilize broker Unix-socket permission test against path-length limits

**Priority:** P1
**Phase:** Phase 14 — Release 0.4.0 Readiness
**Effort:** 0.5-1h
**Dependencies:** FU-P13-T12
**Status:** Selected

## Description

Harden the broker socket-permission regression test so it remains valid on macOS
and CI environments where pytest temp paths can exceed AF_UNIX path limits.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
