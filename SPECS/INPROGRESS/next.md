# Next Task: FU-P12-T1-2 — Add code comment clarifying stdin-only client capture in `on_request`

**Priority:** P3
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 15-30 minutes
**Dependencies:** P12-T1
**Status:** Selected

## Description

In `src/mcpbridge_wrapper/__main__.py` `on_request()`, initialize client info is
captured only for stdin-originated client requests. Add a brief comment near
the capture block so maintainers understand that this intentionally does not
inspect outbound stdout traffic.

## Next Step

Run the PLAN command to create the task PRD with deliverables and acceptance
criteria.
