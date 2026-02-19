# Next Task: FU-P13-T13 — Make broker startup transactional when transport bind/start fails

**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Effort:** 2–3h
**Dependencies:** P13-T2 (✅), P13-T3 (✅)
**Status:** Selected

## Description

Harden `BrokerDaemon.start()` so that partial startup failures (e.g. socket bind errors after the upstream process has already been launched) perform a full rollback: terminate the upstream subprocess, wait for it to exit, remove PID and socket files, and return the broker to a safe STOPPED state without orphaned processes or stale files.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
