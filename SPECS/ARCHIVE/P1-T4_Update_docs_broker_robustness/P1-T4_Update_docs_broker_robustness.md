# P1-T4 — Update docs to reflect broker robustness improvements (P2-T1 – P2-T5)

**Status:** In Progress
**Priority:** P2
**Dependencies:** P2-T1, P2-T2, P2-T4, P2-T5 (all completed 2026-03-01)
**Branch:** feature/P1-T4-docs-broker-robustness

---

## Background

Phase 2 broker robustness tasks shipped four user-visible behaviour changes that the existing documentation does not reflect:

| Task | Change |
|------|--------|
| P2-T1 | `--broker` flag introduced as the single recommended proxy mode (auto-detects connect vs spawn). `--broker-spawn` and `--broker-connect` become legacy aliases. |
| P2-T2 | `--broker` / `--broker-spawn` now detect and remove stale socket/PID files automatically before spawning. Manual cleanup is only needed for `--broker-connect`. |
| P2-T4 | When the broker is unreachable, the proxy writes a JSON-RPC `-32001` error response to stdout instead of silently hanging. |
| P2-T5 | When `--broker --web-ui` is used but the running daemon was started without `--web-ui`, the proxy prints an actionable warning to stderr. |

The README was already updated to use `--broker` everywhere (completed in P2-T1). The individual `docs/` files and their DocC mirrors were not.

---

## Scope

### Files to update

| File | Changes needed |
|------|---------------|
| `docs/broker-mode.md` | Add `--broker` to mode table; update topology, client examples, migration, and limitations sections |
| `docs/troubleshooting.md` | Update "Could not connect" entry (JSON-RPC error + auto-recovery note); update "Stale recovery" entry; add "Warning: broker without --web-ui" entry; update rollback entry |
| `docs/cursor-setup.md` | Replace broker mode section with `--broker` primary / `--broker-connect` advanced; update migration note |
| `docs/claude-setup.md` | Same as cursor-setup |
| `docs/codex-setup.md` | Same as cursor-setup |
| `Sources/.../CursorSetup.md` | DocC mirror of cursor-setup changes |
| `Sources/.../ClaudeCodeSetup.md` | DocC mirror of claude-setup changes |
| `Sources/.../CodexCLISetup.md` | DocC mirror of codex-setup changes |
| `Sources/.../Troubleshooting.md` | DocC mirror of troubleshooting changes |

### Files NOT in scope

- `README.md` — already updated (P2-T1)
- Source code — documentation-only task
- `docs/webui-setup.md`, `docs/architecture.md` — no relevant changes in P2-T1–T5

---

## Deliverables

1. **9 updated markdown files** — all doc and DocC changes applied
2. **`SPECS/INPROGRESS/P1-T4_Validation_Report.md`** — quality gate results

---

## Acceptance Criteria

- [ ] `docs/broker-mode.md` mode table includes `--broker` as primary recommended flag
- [ ] `--broker-connect` and `--broker-spawn` described as legacy aliases in broker-mode.md
- [ ] Broker mode limitations section no longer says stale files require manual cleanup
- [ ] `docs/troubleshooting.md` "Could not connect" entry shows JSON-RPC -32001 error format
- [ ] `docs/troubleshooting.md` "Stale recovery" entry notes auto-recovery for `--broker`
- [ ] `docs/troubleshooting.md` contains new "Warning: broker running without --web-ui" entry
- [ ] All three client setup docs show `--broker` as the recommended broker option
- [ ] DocC sync check passes: `make doccheck-all` exits 0
- [ ] `ruff check src/` passes (no source changes, should be clean)
- [ ] `pytest` passes (no source changes, should be clean)

---

## Implementation Notes

- All doc changes are documentation-only; no Python source files are modified.
- The DocC files in `Sources/XcodeMCPWrapper/Documentation.docc/` are mirrors of the `docs/` files; the project's `make doccheck-all` gate enforces their sync.
- The `--broker-spawn` and `--broker-connect` flags remain valid (backwards-compatible aliases); docs should note this rather than omit them entirely.
