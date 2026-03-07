## REVIEW REPORT — Broker Console Startup

**Scope:** origin/main..HEAD
**Files:** 10

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues
- None.

### Secondary Issues
- [Medium] `src/mcpbridge_wrapper/__main__.py`: `_run_broker_console()` normalizes
  `KeyboardInterrupt` to exit code `0` only after the spawn-and-wait path. When
  `--broker-console` reuses an already healthy broker-backed dashboard, it
  returns `run_tui(runtime)` directly, so `Ctrl-C` bubbles out differently from
  both `--tui` mode and the spawned broker-console path. The reuse path should
  wrap `run_tui(runtime)` in the same `try/except KeyboardInterrupt` handling
  and add regression coverage.

### Architectural Notes
- The new mode correctly stays as orchestration around existing daemon/dashboard
  primitives instead of introducing another broker lifecycle.
- The broker-backed dashboard probe is the right readiness gate for future
  doctor and orchestration work because it validates ownership, not just a
  listening TCP port.

### Tests
- `pytest` passed: `854 passed, 5 skipped`
- `ruff check src/ tests/` passed
- `mypy src/` passed
- `pytest --cov=src --cov-report=term` passed with `91.72%` coverage

### Next Steps
- Add a small follow-up task to align `KeyboardInterrupt` handling across both
  broker-console attach paths.
