# Next Task: FU-P13-T4-1 — Fix asyncio.get_event_loop() deprecation in BrokerProxy

**Priority:** P2
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 1 hour
**Dependencies:** P13-T4
**Status:** Selected

## Description

Replace deprecated `asyncio.get_event_loop()` usage with `asyncio.get_running_loop()` in `src/mcpbridge_wrapper/broker/proxy.py` to align with Python 3.10+ asyncio guidance and avoid deprecation warnings.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
