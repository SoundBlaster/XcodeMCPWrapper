## REVIEW REPORT — FU-REBUILD-P10-T1-5 Documentation Paths

**Scope:** HEAD~5..HEAD (5 commits on `claude/add-mcp-validation-task-X2koZ`)
**Files:** 22 changed (+788 -29)

### Summary Verdict
- [x] Approve with comments

### Critical Issues

None.

### Secondary Issues

- [Medium] `install.sh` uses `which python3` after activating venv, which embeds the absolute path of the venv Python into the wrapper. If the repo is moved or the venv is recreated, the `~/bin/xcodemcpwrapper` wrapper will break and need to be re-run. This is acceptable for a development tool but could be documented in a troubleshooting note.
- [Low] The Kimi CLI section in README.md was not updated with local dev options (consistent with other Kimi limitations documented in BUG-T1, so this is intentional).

### Architectural Notes

- The fix correctly separates three installation paths: (1) uvx/pip for end users, (2) install.sh for ~/bin wrapper, (3) venv for local development. Each path now has its own documentation trail.
- The embedded Python path approach is the standard pattern used by pip-generated entry points (they also hardcode the Python path in their shebang).

### Tests

- 321 passed, 5 skipped — no regressions.
- No new tests needed (documentation-only changes + install script).
- `ruff check src/` clean.
- `mypy src/` has 4 pre-existing errors (unchanged from baseline).

### Next Steps

- No blocking follow-up actions required.
- Optional: Add troubleshooting note about re-running install.sh if repo is moved.
