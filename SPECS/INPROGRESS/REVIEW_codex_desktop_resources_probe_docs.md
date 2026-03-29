## REVIEW REPORT — P1-T14 Codex Desktop Resources Probe Docs

**Scope:** `origin/main..HEAD`
**Files:** 11

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

- The docs now distinguish protocol-surface probe behavior (`resources/*`) from
  actual tools connectivity, which reduces false-negative troubleshooting in
  Codex Desktop flows.
- Markdown and DocC mirrors were updated together for the affected surfaces
  (README overview, troubleshooting, Codex setup), and `doccheck-all` confirms
  synchronization.

### Tests

- `pytest` — PASS (`923 passed, 5 skipped`)
- `ruff check src/` — PASS
- `mypy src/` — PASS
- `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` — PASS (`91.62%`)
- `make doccheck-all` — PASS

### Next Steps

- No actionable review findings. FOLLOW-UP is skipped.
