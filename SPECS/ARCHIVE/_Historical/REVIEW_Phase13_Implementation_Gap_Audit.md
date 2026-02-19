## REVIEW REPORT — Phase 13 Implementation Gap Audit

**Scope:** Final implementation phase review (`Phase 13: Persistent Broker & Shared Xcode Session`, including P13-T1..P13-T6 and linked follow-ups)  
**Primary Sources:** `SPECS/Workplan.md`, `SPECS/ARCHIVE/P13-T*_*/`, `src/mcpbridge_wrapper/broker/*`, `src/mcpbridge_wrapper/__main__.py`, `docs/broker-mode.md`

### Summary Verdict
- [ ] Approve
- [ ] Approve with comments
- [x] Request changes
- [ ] Block

### Critical / High Findings

1. **[High] `--broker-spawn` auto-start path is not functionally complete (`--broker-daemon` entrypoint missing).**
   - `BrokerProxy` spawns `python -m mcpbridge_wrapper --broker-daemon`: `src/mcpbridge_wrapper/broker/proxy.py:135`.
   - `main()` only parses `--broker-connect` / `--broker-spawn`; no daemon-mode branch exists: `src/mcpbridge_wrapper/__main__.py:192`, `src/mcpbridge_wrapper/__main__.py:271`, `src/mcpbridge_wrapper/__main__.py:273`.
   - Unknown flags are forwarded to upstream bridge command in direct path: `src/mcpbridge_wrapper/bridge.py:38`.
   - Result: spawned process does not become a broker daemon and auto-spawn can timeout instead of creating the socket.
   - Gap type: missed/lost feature versus expected runtime behavior in P13-T4/P13-T6 broker adoption flow.

2. **[High] JSON-RPC numeric request IDs are lossy/collision-prone due 20-bit masking.**
   - Integer IDs are truncated: `int_id = original_id & _ID_MASK`: `src/mcpbridge_wrapper/broker/transport.py:306`.
   - Response restoration returns lower 20 bits unless mapped as string: `src/mcpbridge_wrapper/broker/transport.py:397`.
   - Impacts:
     - IDs larger than `0xFFFFF` are mutated in responses.
     - Negative integer IDs are transformed.
     - Distinct large IDs can collide within one session.
   - Gap type: functional protocol correctness risk under valid JSON-RPC ID patterns.

### Secondary Findings

3. **[Medium] Planned local security boundary is documented but not enforced in transport.**
   - Architecture/ADR specifies same-UID verification via `getpeereid` and owner-only socket permissions:  
     `SPECS/ARCHIVE/P13-T1_Design_persistent_broker_architecture_and_protocol_contract/P13-T1_Design_persistent_broker_architecture_and_protocol_contract.md:55`,  
     `SPECS/ARCHIVE/P13-T1_Design_persistent_broker_architecture_and_protocol_contract/P13-T1_Design_persistent_broker_architecture_and_protocol_contract.md:201`.
   - Runtime currently accepts clients without UID validation; `peer_uid` is derived from `peername` and not enforced: `src/mcpbridge_wrapper/broker/transport.py:189`, `src/mcpbridge_wrapper/broker/transport.py:201`.
   - Socket mode is not explicitly set to `0600` after bind: `src/mcpbridge_wrapper/broker/transport.py:77`.
   - Gap type: security hardening feature not closed.

4. **[Medium] Broker startup is not atomic if transport startup fails after upstream launch.**
   - In `start()`, upstream launch + PID file write occur before transport bind/start: `src/mcpbridge_wrapper/broker/daemon.py:109`, `src/mcpbridge_wrapper/broker/daemon.py:112`, `src/mcpbridge_wrapper/broker/daemon.py:127`.
   - If `transport.start()` raises, `start()` exits without cleanup of upstream process or PID/socket state.
   - Gap type: reliability/lifecycle issue under bind/permission/race failures.

5. **[Medium] Core Phase 13 objective remains partially unverified (prompt reduction acceptance not closed).**
   - Workplan still marks P13-T5 as partial and leaves manual prompt criterion unchecked: `SPECS/Workplan.md:2102`, `SPECS/Workplan.md:2114`.
   - Validation report confirms unresolved interactive verification: `SPECS/ARCHIVE/P13-T5_Validate_prompt_reduction_and_multi_client_stability/P13-T5_Validation_Report.md:26`.
   - Gap type: incomplete closure of the main UX outcome this phase targets (reduced repeated Xcode permission prompts).

6. **[Low] Operational “broker status/start/stop” is documented as shell/python one-liners, not first-class CLI mode.**
   - Workplan output expected health/status command: `SPECS/Workplan.md:2001`.
   - Current guide relies on long inline commands including private attribute mutation (`d._transport=t`): `docs/broker-mode.md:28`, `docs/broker-mode.md:42`, `docs/broker-mode.md:54`.
   - Gap type: maintainability/operability mismatch vs intended productized flow.

### Tests and Coverage Gaps

- Missing end-to-end runtime test that `--broker-spawn` actually creates a live broker socket (not only mocked spawn paths).
- Missing transport tests for large/negative integer request IDs to ensure identity preservation.
- Missing tests for UID rejection behavior (if security boundary is intended to be enforced).
- Missing failure-path test for `BrokerDaemon.start()` where `transport.start()` fails after upstream launch.

### Recommended Follow-Up Tasks

1. Implement explicit daemon CLI mode (`--broker-daemon` or `broker host`) in `main()` and add E2E spawn validation.
2. Replace lossy int-bitmask remap with reversible per-session int-ID mapping (parallel to string ID map), then add regression tests.
3. Enforce local auth boundary (`getpeereid` same-UID check) and explicit socket permission hardening (`chmod 0600`) with tests.
4. Make `BrokerDaemon.start()` transactional (cleanup on partial startup failure).
5. Complete P13-T5 interactive desktop validation and update verdict from PARTIAL to PASS/FAIL with evidence.

