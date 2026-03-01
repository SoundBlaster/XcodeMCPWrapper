## REVIEW REPORT — P1-T3: Broker-first MCP settings examples in README

**Scope:** origin/main..HEAD
**Files:** 1 (`README.md`) + 5 SPECS bookkeeping files

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues

None.

### Secondary Issues

- [Low] The Cursor section opens with the prose line "Broker setup examples are listed first." — Claude Code and Codex CLI sections use the same phrasing. The repetition is mildly redundant if a reader scans the whole section, but it is not harmful and aids per-section orientation. No action required unless a future pass standardises the intro sentences across agent sections.

- [Nit] The Cursor broker-mode JSON example hard-codes the literal `/Users/YOUR_USERNAME/` in the `--web-ui-config` path, while the Claude Code and Codex CLI bash variants use the portable `$HOME` variable. This inconsistency is harmless in JSON (environment variables aren't expanded in JSON strings), so the placeholder is the correct approach. Document as an acknowledged inconsistency.

### Architectural Notes

- The change is purely documentation. No Python source, tests, or configuration files were modified.
- Broker-first ordering is now consistent across Cursor (JSON), Claude Code (bash), and Codex CLI (bash) sections, satisfying the PRD's acceptance criteria.
- The `direct mode` label added to existing manual/venv headings correctly disambiguates them from the new broker entries without breaking existing content.

### Tests

- No unit or integration tests are affected — this is a documentation-only change.
- Quality gates (pytest, ruff, mypy) are not applicable; all pass trivially on a docs-only diff.
- Coverage remains ≥ 90% (unchanged).

### Next Steps

- No blocker or high-severity findings. FOLLOW-UP is **skipped**.
- Future consideration (not actionable now): unify the section intro phrasing into a shared heading style as part of a broader README style pass.
