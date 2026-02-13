## REVIEW REPORT — FU-P9-T4-1 publish_helper protected-main guidance

**Scope:** `origin/main..HEAD`  
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
- The release-helper guidance now matches protected-branch workflows and no longer implies direct commits/tags from `main`.
- Changes are appropriately scoped to command guidance text, unit coverage, and workflow artifacts.

### Tests
- `pytest` passed (`345 passed, 5 skipped`).
- `ruff check src/` passed.
- `mypy src/` passed.
- `pytest --cov` passed with **96.62%** total coverage (>= 90%).

### Next Steps
- No actionable findings.
- FOLLOW-UP step is skipped.
