# Next Task: FU-BUG-T7-1 — Cap `pending_methods` map to guard against unbounded growth

**Priority:** P3
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 1-2 hours
**Dependencies:** BUG-T7
**Status:** Selected

## Description

Harden `pending_methods` tracking in `src/mcpbridge_wrapper/__main__.py` so it cannot
grow unbounded under abnormal traffic patterns (e.g. bridge crash or one-way
messages), while preserving BUG-T7 method-correlation behavior.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
