## REVIEW REPORT — P1-T4 docs broker robustness

**Scope:** origin/main..HEAD (5 commits)
**Files:** 9 markdown files (5 docs/, 4 DocC mirrors)
**Date:** 2026-03-01

---

### Summary Verdict
- [ ] Approve
- [x] Approve with comments
- [ ] Request changes
- [ ] Block

All primary acceptance criteria are met. Two minor gaps found — one missed update in `docs/troubleshooting.md` and one out-of-scope file pair that are now inconsistent.

---

### Critical Issues

None.

---

### Secondary Issues

**[Medium] `docs/troubleshooting.md` "MCP tools are green, but dashboard is unreachable" section not updated**

Lines 309 and 334 still reference `--broker-spawn` as the primary flag:

```
- `--broker-connect` never starts a dashboard by itself; `--broker-spawn --web-ui` only starts one when it must spawn a host.
```

```
3. **Unified broker single-config:** use `--broker-spawn --web-ui --web-ui-config <shared-path>` in all clients…
```

The DocC mirror (`Sources/.../Troubleshooting.md`) was correctly updated to `--broker` for both of these lines during EXECUTE, but the `docs/troubleshooting.md` source was not. This creates a sync divergence between the two files that `make doccheck-all` does not catch (the check enforces that docs → DocC updates happen together, but does not detect the reverse).

**Fix:** Update both occurrences in `docs/troubleshooting.md` to match the DocC mirror.

---

**[Low] `docs/webui-setup.md` and its DocC mirror `WebUIDashboard.md` not updated**

Both files still use `--broker-spawn` in their multi-agent setup examples (lines 101 and 107 in each):

```
use `--broker-spawn --web-ui --web-ui-config <shared-path>` across Cursor/Zed/Claude/Codex
```

These files were explicitly excluded from scope in the P1-T4 PRD ("docs/webui-setup.md — no relevant changes in P2-T1–T5"). However, the guidance is now inconsistent with all other broker docs that use `--broker`.

**Fix:** Update `docs/webui-setup.md` and `Sources/.../WebUIDashboard.md` to use `--broker` in multi-agent examples in a follow-up task.

---

### Architectural Notes

- The `--broker-spawn` legacy alias correctly remains visible in the docs in backward-compat contexts (rollback instructions, stale-recovery notes, "Warning: broker without --web-ui" cause explanation). These references are accurate and should not be removed.
- DocC sync enforcement (`make doccheck-all`) catches docs→DocC divergence but not DocC→docs divergence. The medium finding above was only caught by manual grep. The sync script could be enhanced to check both directions, but that is out of scope here.

---

### Tests

- `pytest`: 737 passed, 5 skipped — no regressions (documentation-only change)
- `ruff check src/`: clean — no source changes
- `pytest --cov`: 91.3% — above 90% threshold
- `make doccheck-all`: passed — DocC mirrors in sync for all changed `docs/` files

---

### Next Steps

1. **Follow-up task (Medium):** Fix 2 remaining `--broker-spawn` references in `docs/troubleshooting.md` "MCP tools are green" section.
2. **Follow-up task (Low):** Update `docs/webui-setup.md` and `Sources/.../WebUIDashboard.md` multi-agent examples to use `--broker`.
