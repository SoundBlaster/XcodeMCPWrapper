## REVIEW REPORT — P3-T11 Web UI Stop Control

**Scope:** origin/main..HEAD  
**Files:** 12

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

- Control-plane API (`/api/control`, `/api/control/stop`) is capability-driven and opt-in via callback wiring, which avoids unsafe stop behavior in unsupported runtime modes.
- Broker-daemon stop is routed through delayed self-SIGTERM from a helper thread so HTTP response can complete before shutdown starts.

### Tests

- `pytest` passed (`740 passed, 5 skipped`)
- `ruff check src/` passed
- `mypy src/` passed
- `pytest --cov` passed (`91.01%`, threshold >= 90%)

### Next Steps

- FOLLOW-UP skipped: no actionable findings.
