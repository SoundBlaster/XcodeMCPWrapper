# Active Task: BUG-T8

## Task Metadata
- **ID:** BUG-T8
- **Name:** Audit log dashboard shows only entries from current process (per-process in-memory storage)
- **Priority:** P0
- **Status:** In Progress
- **Branch:** feature/BUG-T8-audit-log-cross-process-visibility
- **Started:** 2026-02-15

## Summary
Fix `AuditLogger` so the web UI dashboard reflects audit entries from all wrapper processes,
not just the process currently serving the web UI. In multi-process setups (Cursor, Zed),
the process owning the web UI port has a separate in-memory `_entries` list from sibling
processes that actually handle MCP tool calls.

## Approach
Option A: On `AuditLogger.__init__`, load the most recent N entries from existing JSONL
files in `log_dir` into `self._entries`. This gives historical visibility on startup with
minimal complexity, and aligns with Phase 13's direction (persistent broker will eventually
collapse multi-process into one).

## Dependencies
- BUG-T6 ✅ (port collision fix — precondition for this bug to manifest)
- P10-T1 ✅ (AuditLogger implementation)

## Recently Archived
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (PASS)
- 2026-02-15 — FU-BUG-T6-1: Document stale-process cleanup (PASS)
- 2026-02-14 — BUG-T7: resources/* error normalization (PASS)
- 2026-02-14 — BUG-T6: Web UI port collisions create unstable multi-process behavior (PASS)
