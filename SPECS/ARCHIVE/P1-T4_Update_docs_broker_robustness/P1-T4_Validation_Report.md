# P1-T4 Validation Report

**Task:** Update docs to reflect broker robustness improvements (P2-T1 – P2-T5)
**Date:** 2026-03-01
**Verdict:** PASS

---

## Quality Gates

| Gate | Result | Detail |
|------|--------|--------|
| `pytest` | ✅ PASS | 737 passed, 5 skipped, 2 warnings |
| `ruff check src/` | ✅ PASS | All checks passed |
| `pytest --cov` | ✅ PASS | 91.3% coverage (≥90% required) |
| `make doccheck-all` | ✅ PASS | DocC sync verified across all scopes |

---

## Files Changed

| File | Change summary |
|------|---------------|
| `docs/broker-mode.md` | Added `--broker` to mode table; updated topology, Web UI note, client examples (Cursor/Zed/Claude/Codex), migration and rollback sections; rewrote Limitations to note auto-recovery |
| `docs/troubleshooting.md` | Updated "Could not connect" (JSON-RPC error + auto-recovery note); updated "Stale recovery" (auto for `--broker`); added "Warning: broker without --web-ui" entry; updated rollback entry |
| `docs/cursor-setup.md` | Merged two broker sections into `--broker` primary + `--broker-connect` advanced; updated migration note and troubleshooting entry |
| `docs/claude-setup.md` | Same pattern as cursor-setup |
| `docs/codex-setup.md` | Same pattern as cursor-setup |
| `Sources/.../CursorSetup.md` | DocC mirror of cursor-setup changes |
| `Sources/.../ClaudeCodeSetup.md` | DocC mirror of claude-setup changes |
| `Sources/.../CodexCLISetup.md` | DocC mirror of codex-setup changes |
| `Sources/.../Troubleshooting.md` | DocC mirror of troubleshooting changes including new web-UI mismatch entry |

---

## Acceptance Criteria

- [x] `docs/broker-mode.md` mode table includes `--broker` as primary recommended flag
- [x] `--broker-connect` and `--broker-spawn` described as legacy aliases in broker-mode.md
- [x] Broker mode limitations section no longer says stale files require manual cleanup
- [x] `docs/troubleshooting.md` "Could not connect" entry shows JSON-RPC -32001 error format
- [x] `docs/troubleshooting.md` "Stale recovery" entry notes auto-recovery for `--broker`
- [x] `docs/troubleshooting.md` contains new "Warning: broker running without --web-ui" entry
- [x] All three client setup docs show `--broker` as the recommended broker option
- [x] DocC sync check passes: `make doccheck-all` exits 0
- [x] `ruff check src/` passes
- [x] `pytest` passes
