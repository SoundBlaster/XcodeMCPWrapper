## REVIEW REPORT — T-011 Synthetic Broker Tools/List Changed

**Scope:** `1b48065..HEAD`  
**Files:** 10

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

- None.

### Secondary Issues

- None.

### Architectural Notes

- Reusing the existing broker warm-up probe loop is the correct choice. It avoids a second
  polling mechanism and keeps readiness logic centralized in the daemon.
- Queueing the synthetic `notifications/tools/list_changed` until the client sends
  `notifications/initialized` preserves MCP lifecycle ordering and avoids emitting a late-ready
  signal into a pre-initialized session.
- Fingerprinting the non-empty catalog before broadcasting keeps reconnect behavior quiet when
  the tool catalog is unchanged, which matches the task goal of signaling meaningful change
  rather than probe churn.
- Residual interoperability risk remains client-side: some MCP clients may still ignore
  `notifications/tools/list_changed` or require a manual reconnect despite the broker now
  behaving correctly at the protocol layer.

### Tests

- `pytest tests/unit/test_broker_daemon.py tests/unit/test_broker_transport.py -q` — PASS (`116 passed`)
- `ruff check src/` — PASS
- `mypy src/` — PASS
- `pytest` — PASS (`920 passed, 5 skipped, 2 warnings`)
- `pytest --cov` — PASS (`920 passed, 5 skipped`; coverage `91.57%`)

### Next Steps

- No actionable review findings. FOLLOW-UP is skipped.
