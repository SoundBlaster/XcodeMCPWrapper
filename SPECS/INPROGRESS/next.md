# Next Task: FU-P13-T4-2 — Implement or remove reconnect parameter in BrokerProxy

**Priority:** P2
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session
**Effort:** 1 hour
**Dependencies:** P13-T4
**Status:** Selected

## Description

Address dead configuration in `BrokerProxy` where `reconnect` is accepted and stored but not used by bridge execution. Implement a single reconnect retry on broken broker connection or remove the parameter and clean up the API/tests so behavior is explicit.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
