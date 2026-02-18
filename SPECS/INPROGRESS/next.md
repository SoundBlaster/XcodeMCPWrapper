# Next Task: P13-T5 — Validate prompt reduction and multi-client stability

**Priority:** P1  
**Phase:** Phase 13: Persistent Broker & Shared Xcode Session  
**Effort:** TBD  
**Dependencies:** P13-T4 (Complete)  
**Status:** Selected

## Description

Add integration tests and manual validation that repeated short-lived MCP clients reuse the single broker-owned upstream bridge, confirm multi-client stability under load, and document any prompt-related behavioral changes to prove that broker mode avoids extra Xcode permission prompts.

## Next Step

Run the PLAN command to create `SPECS/INPROGRESS/P13-T5_Validate_prompt_reduction_and_multi_client_stability.md` with the verification checklist, needed metrics, and any follow-up notes; then proceed with the integration/validation work.

## Recently Archived

- 2026-02-18 — P13-T4: Add stdio proxy mode for compatibility with existing MCP clients (PASS)
- 2026-02-18 — P13-T3: Implement multi-client transport and JSON-RPC multiplexing (PASS)
- 2026-02-17 — P13-T2: Implement persistent broker daemon with single upstream Xcode bridge (PASS)
- 2026-02-16 — P13-T1: Design persistent broker architecture and protocol contract (PASS)
- 2026-02-16 — FU-P13-T8: Prevent Web UI port collision from destabilizing MCP sessions (PASS)
