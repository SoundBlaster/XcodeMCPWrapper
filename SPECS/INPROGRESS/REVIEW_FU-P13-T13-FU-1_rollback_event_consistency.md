## REVIEW REPORT — FU-P13-T13-FU-1 rollback event consistency

**Scope:** `origin/main..HEAD`
**Files:** 7

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

None.

### Secondary Issues

None.

### Architectural Notes

- `_rollback_startup()` now aligns state and signaling contracts by setting both `_stop_event` and `_stopped_event` when rollback transitions the daemon to `STOPPED`.
- The added regression test directly exercises transport startup failure and validates defensive event consistency.

### Tests

- `TMPDIR=/tmp pytest` → 624 passed, 5 skipped
- `ruff check src/` → pass
- `mypy src/` → pass
- `TMPDIR=/tmp pytest --cov` → 91.70% total coverage (>=90%)

### Next Steps

- FOLLOW-UP skipped: no actionable review findings.
