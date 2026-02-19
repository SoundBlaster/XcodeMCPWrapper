# Next Task: FU-P13-T15 — Restore broker same-UID client acceptance when peer credential APIs are unavailable

**Priority:** P1
**Phase:** Phase 13 — Persistent Broker & Shared Xcode Session
**Effort:** 2-4h
**Dependencies:** FU-P13-T12 (✅), FU-P13-T14 (✅)
**Status:** Selected

## Description

Broker mode currently rejects same-user local clients with `-32003 UID mismatch`
when peer credential lookup returns `Errno 42 (Protocol not available)`. Add a
platform-safe credential verification fallback that preserves security
boundaries while allowing same-UID local clients to connect.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
