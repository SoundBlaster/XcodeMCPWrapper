# Next Task: FU-P13-T2-2 — Move PID file write to after successful upstream launch

**Priority:** P3
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 1 hour
**Dependencies:** P13-T2
**Status:** Selected

## Description

Move PID file write in `BrokerDaemon.start()` to execute only after `_launch_upstream()`
completes successfully, preventing stale live-PID locks when launch fails mid-startup.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
