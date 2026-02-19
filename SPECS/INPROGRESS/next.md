# Next Task: FU-P13-T11 — Preserve JSON-RPC numeric request ID fidelity in broker transport

**Priority:** P1
**Phase:** Phase 13 follow-up (broker transport)
**Effort:** 2h
**Dependencies:** P13-T3 (✅ complete)
**Status:** Selected

## Description

Remove lossy 20-bit integer ID masking in broker request remapping and implement a reversible per-session ID mapping for numeric IDs so all valid JSON-RPC IDs round-trip exactly.

Currently `_process_client_line` applies `original_id & 0xFFFFF` to integer request IDs before encoding them into the broker composite ID. This silently truncates any integer outside the 20-bit range and aliases distinct IDs that share the same lower 20 bits. Negative IDs are also mangled. The fix replaces the bitmask with a per-session incrementing counter (already used for string IDs) and stores a reverse mapping so the response path can restore the exact original value in O(1).

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
