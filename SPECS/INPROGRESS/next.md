# Next Task: FU-P12-T1-3 — Show multi-client widgets in Web UI instead of single overwritten active client

**Priority:** P2
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 2-4 hours
**Dependencies:** P12-T1
**Status:** Selected

## Description

The dashboard currently exposes one global active client that gets overwritten
by the latest `initialize` handshake. Add multi-client visibility so the UI
shows one widget per detected client (with metadata like last seen and usage)
instead of a single mutable value.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
