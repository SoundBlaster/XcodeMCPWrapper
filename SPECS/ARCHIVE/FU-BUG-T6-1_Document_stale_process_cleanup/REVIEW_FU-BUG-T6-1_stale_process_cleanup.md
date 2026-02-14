## REVIEW REPORT — FU-BUG-T6-1 stale-process cleanup documentation

**Scope:** origin/main..HEAD (4 commits)
**Date:** 2026-02-15
**Files changed:** `docs/troubleshooting.md` (docs only), SPECS artifacts

---

### Summary Verdict

- [x] Approve

---

### Critical Issues

None.

---

### Secondary Issues

None.

---

### Architectural Notes

- The new section correctly matches both warning variants emitted by `__main__.py` at lines 261–262 (bridge+webui mode) and lines 238–239 (`--web-ui-only` mode). Quoting the exact strings ensures users can match the output to the troubleshooting entry.
- Placement after the `zsh: no matches found` section and before the "Uptime still shows 1h 0m 0s" section is logical — all three are Web UI operational issues grouped together.
- `pkill -f mcpbridge` is a broad kill-all approach. It is safe here because it targets `mcpbridge` process names and there are no other system processes with that name. The note about multiple processes on different ports adds appropriate caution.
- The `lsof -i TCP:$PORT -sTCP:LISTEN` command is macOS-specific, which is fine because this project targets macOS/Xcode exclusively.

---

### Tests

- This is a docs-only change; no test changes are required.
- Quality gate results at time of execute:
  - `ruff check src/`: ✅ All checks passed
  - `pytest`: ✅ 369 passed, 5 skipped
  - Coverage: ✅ 96.2% (requirement ≥ 90%)

---

### Next Steps

No actionable findings. FOLLOW-UP step is skipped.
