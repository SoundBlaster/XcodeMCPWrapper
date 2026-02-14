# Active Task: BUG-T7

**Task ID:** BUG-T7
**Title:** Unsupported `resources/*` methods can return non-standard error shape
**Branch:** feature/BUG-T7-resources-error-normalization
**Status:** 🟡 In Progress
**Priority:** P0
**Selected:** 2026-02-14

## Description

For unsupported methods like `resources/list` and `resources/templates/list`, upstream returns
tool-style `result.isError/content` payloads instead of JSON-RPC `error`. Some clients classify
this as unexpected response type.

## Resolution Path

- [ ] Implement FU-P13-T9
- [ ] Add method-aware normalization regression tests
- [ ] Validate strict-client compatibility for `resources/*` probing

## Recently Archived

- 2026-02-14 — BUG-T6: Web UI port collisions create unstable multi-process behavior (PASS)
- 2026-02-14 — BUG-T5: Empty-content tool results can still violate strict `structuredContent` contract (PASS)
- 2026-02-14 — BUG-T3: Web UI cannot stay available when MCP bridge initialization fails (PASS)
- 2026-02-14 — BUG-T2: codex mcp add with Web UI extras fails in zsh (PASS)
- 2026-02-13 — FU-P9-T2-2: Add troubleshooting guidance for stale uvx cache/process versions (PASS)
- 2026-02-13 — FU-P9-T4-1: Align publish_helper output with protected main branch workflow (PASS)
- 2026-02-13 — P9-T4: Create the publishing helper (PASS)
