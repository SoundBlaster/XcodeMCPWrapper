# PRD: P13-T6 — Document broker mode configuration, migration, and rollback

**Status:** IN PROGRESS
**Priority:** P1
**Branch:** `feature/P13-T6-broker-mode-docs`
**Depends on:** P13-T4 ✅

---

## 1. Overview

P13-T4 introduced broker/proxy runtime modes, but adoption guidance is still fragmented. P13-T6 documents how to enable broker mode across supported clients, how to operate it safely, and how to rollback to direct mode without downtime.

This task delivers practical setup snippets, migration steps, stop/status flows, troubleshooting for broker socket/lock issues, and explicit rollback commands for Cursor, Claude Code, and Codex CLI users.

---

## 2. Scope

### In-scope
- Add broker mode docs in README and setup guides for Cursor, Claude Code, and Codex CLI.
- Add one-command broker lifecycle flows (start/stop/status/logs) for local/manual users.
- Add migration checklist from direct mode to broker mode.
- Add rollback guide from broker mode back to direct mode.
- Add troubleshooting entries for stale broker socket/lock/PID recovery.
- Provide broker-mode config templates for supported clients.

### Out-of-scope
- New broker runtime behavior or protocol changes.
- Non-doc code refactors unrelated to task documentation.
- End-to-end interactive Xcode prompt verification (already tracked under P13-T5).

---

## 3. Design

### 3.1 Documentation model

Create a dedicated broker-mode guide (`docs/broker-mode.md`) and link to it from README and per-client setup docs. Keep setup docs short and focused on client-specific config snippets while centralizing lifecycle/troubleshooting details in the broker guide.

### 3.2 Migration and rollback flows

Provide explicit before/after MCP config examples and command-level rollback instructions:
- Direct mode (`mcpbridge-wrapper` only)
- Broker host mode (`mcpbridge-wrapper --broker-mode host`)
- Broker client mode (`mcpbridge-wrapper --broker-mode client`)

Include operational commands (`start`, `status`, `logs`, `stop`) using current CLI options.

### 3.3 Templates

Add broker-ready templates under `config/` for Cursor JSON and CLI snippets for Claude/Codex to reduce copy/paste errors.

---

## 4. File changes

| File | Change |
|------|--------|
| `README.md` | Add broker mode overview + link + quick migration/rollback pointers |
| `docs/broker-mode.md` | New deep-dive broker mode guide (config, ops, migration, rollback, troubleshooting) |
| `docs/cursor-setup.md` | Add broker mode config examples and rollback note |
| `docs/claude-setup.md` | Add broker mode add/remove examples |
| `docs/codex-setup.md` | Add broker mode add/remove examples |
| `docs/troubleshooting.md` | Add broker socket/lock/PID stale state troubleshooting |
| `config/cursor-mcp-broker.json` | Broker-mode Cursor config template |
| `config/claude-code-broker.txt` | Broker-mode Claude setup template |
| `config/codex-cli-broker.txt` | Broker-mode Codex setup template |
| `SPECS/INPROGRESS/P13-T6_Validation_Report.md` | Quality gates + acceptance criteria evidence |

---

## 5. Acceptance criteria

- [ ] Docs include one-command start/stop/status flows for broker mode
- [ ] Client examples are provided for Codex/Cursor/Claude
- [ ] Troubleshooting includes socket/lock and stale-broker recovery
- [ ] Rollback steps to direct mode are explicit and tested

---

## 6. Quality gates

- `pytest` — all tests pass
- `ruff check src/` — no lint errors
- `mypy src/` — no new type errors
- `pytest --cov` — coverage ≥ 90%
