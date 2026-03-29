# Next Task: P1-T14 — Document Codex Desktop resource-probe behavior for Xcode tools MCP connectivity

**Priority:** P1
**Phase:** Phase 1 — Documentation
**Effort:** 2 hours
**Dependencies:** None
**Status:** Selected

## Description

Codex Desktop can probe `resources/list` and `resources/templates/list` even when
connected to this tools-focused Xcode MCP server. We need explicit guidance that
`-32601 unknown method` on these resource probes can be non-fatal, plus a clear
verification path based on real Xcode tool calls.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
