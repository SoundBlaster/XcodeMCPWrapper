# Next Task: FU-P13-T2-1 — Replace run_forever() polling loop with asyncio.Event-based wait

**Priority:** P3
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 1-2 hours
**Dependencies:** P13-T2
**Status:** Selected

## Description

Replace the `asyncio.sleep(0.1)` polling in `BrokerDaemon.run_forever()` with an `asyncio.Event` wait so stop signaling is immediate and lifecycle handling remains deterministic.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
