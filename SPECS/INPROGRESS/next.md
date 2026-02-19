# Next Task: FU-P13-T12 — Enforce local Unix-socket security boundary for broker clients

**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Effort:** 2–3h
**Dependencies:** P13-T1 (✅), P13-T3 (✅)
**Status:** Selected

## Description

Implement same-UID peer credential verification for broker Unix-socket clients and enforce owner-only socket permissions (`0600`), aligning runtime behavior with the P13-T1 ADR security decisions. Connections from different-UID processes must be rejected without affecting active sessions.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
