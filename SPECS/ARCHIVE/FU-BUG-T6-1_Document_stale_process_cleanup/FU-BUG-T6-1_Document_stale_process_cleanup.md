# FU-BUG-T6-1: Document stale-process cleanup for Web UI port collisions

**Task ID:** FU-BUG-T6-1
**Type:** Follow-Up / Documentation
**Priority:** P2
**Status:** In Progress
**Branch:** feature/FU-BUG-T6-1-stale-process-troubleshooting
**Created:** 2026-02-15
**Depends on:** BUG-T6 (completed)

---

## 1. Context

BUG-T6 introduced port-availability checks so that when the Web UI port is already occupied, the wrapper:
- In bridge+webui mode: prints `Warning: Web UI port {port} is already in use. Skipping Web UI startup — MCP bridge will run without the dashboard.` and continues without the dashboard.
- In `--web-ui-only` mode: prints `Error: Web UI port {port} is already in use. Stop the existing process and retry.` and exits with code 1.

These messages are clear, but users who see them have no guidance on *how* to identify and stop the stale process. This follow-up adds that guidance to `docs/troubleshooting.md`.

---

## 2. Deliverables

| # | Artifact | Location |
|---|----------|----------|
| 1 | New troubleshooting section "Web UI port is already in use" | `docs/troubleshooting.md` |

---

## 3. Acceptance Criteria

- [ ] AC1: Troubleshooting entry title or context clearly references the "port already in use" warning message from BUG-T6 so users can cross-reference.
- [ ] AC2: Entry includes diagnostic commands to identify the process holding the port (e.g., `lsof -i :<port>` or `ps aux | grep mcpbridge`).
- [ ] AC3: Entry includes cleanup steps to kill the stale process.
- [ ] AC4: Entry notes that multiple wrapper processes can coexist (different ports or restarts) and advises verifying the correct PID.
- [ ] AC5: No code changes are required — docs-only change.

---

## 4. Implementation Plan

### 4.1 New section in `docs/troubleshooting.md`

Insert a new section after the existing "Uptime still shows 1h 0m 0s" entry (which covers stale uvx cache), since they are closely related topics.

**Section title:** `### "Web UI port N is already in use"`

**Content outline:**
1. Symptom — show the exact warning/error strings from the source code
2. Cause — stale wrapper process from a previous run, a crashed client restart, or a parallel instance on the same port
3. Diagnosis — `lsof` / `ps` commands to find the PID
4. Recovery — kill the process and restart
5. Note about multiple processes on different ports

---

## 5. Dependencies

- BUG-T6 source code in `src/mcpbridge_wrapper/__main__.py` (already merged to main)
- Existing `docs/troubleshooting.md` structure (already read)

---

## 6. Out of Scope

- No code changes to the wrapper
- No changes to test suite
- No changes to other docs

---
**Archived:** 2026-02-15
**Verdict:** PASS
