## REVIEW REPORT — BUG-T17 audit-log-rows-stay-unfolded

**Scope:** origin/main..HEAD
**Files:** 7

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
- The fix keeps state management local to `dashboard.js` and avoids API contract changes.
- Expansion state is reset on explicit page/filter navigation, reducing stale-row carryover risk.
- Reopening details after refresh re-fetches payload details for expanded rows; this is acceptable for current scale and keeps implementation simple.

### Tests
- Added regression assertion in `tests/unit/webui/test_server.py` to verify audit-row state-preservation logic is present in served frontend bundle.
- Quality gates passed:
  - `PYTHONPATH=src pytest`
  - `ruff check src/`
  - `PYTHONPATH=src mypy src/`
  - `PYTHONPATH=src pytest --cov`
- Coverage remains above threshold: `91.33%`.

### Next Steps
- No actionable review findings.
- FOLLOW-UP step is skipped for BUG-T17.
