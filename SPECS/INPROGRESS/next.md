# Next Task: P6-T2 — Build a terminal frontend for broker daemon monitoring and control

**Priority:** P1
**Phase:** Phase 6: Explicit Broker Frontend
**Dependencies:** P6-T1
**Status:** Ready

## Description

Implement a terminal-first operator interface for the broker daemon so users can explicitly see whether the daemon is running, whether upstream Xcode connectivity is healthy, which clients are attached, and what recent reconnect/error events occurred. The interface should give a clearer operational model than auto-spawn alone.

## Recently Archived

- `P6-T1` — Add explicit broker runtime status surface for frontend consumers (`PASS`, archived 2026-03-07)

## Next Step

Run the PLAN command for `P6-T2` and define the TUI scope, entrypoint, and control flow against the new broker runtime status API.
