# Next Task: P4-T1 — Auto-restart stale broker daemon on version mismatch after upgrade

**Priority:** P0
**Phase:** Phase 4: Broker Lifecycle Management
**Effort:** 6 hours
**Dependencies:** none
**Status:** Selected

## Description

When users upgrade `mcpbridge-wrapper`, older broker daemons can keep running and serve stale behavior to new `--broker` clients. Implement version-aware broker lifecycle handling so stale daemons are detected, restarted automatically, and can be inspected/stopped explicitly via CLI.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
