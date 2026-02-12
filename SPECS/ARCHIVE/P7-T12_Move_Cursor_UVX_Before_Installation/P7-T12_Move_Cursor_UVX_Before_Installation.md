# P7-T12 — Move Cursor IDE uvx Settings Before Installation Instructions in README

**Priority:** P1
**Phase:** Phase 7: Documentation
**Dependencies:** P7-T10

## Objective

Reorder README.md so the Cursor IDE uvx configuration (basic and Web UI variants) appears before the Installation section. Cursor is the primary target client, and most users only need to paste a JSON block into `~/.cursor/mcp.json` — they shouldn't have to scroll through five installation options first.

## Success Criteria

1. The Cursor uvx basic `mcp.json` snippet is visible in the README before the "### Installation" heading.
2. The Cursor uvx-with-Web-UI `mcp.json` snippet (`--web-ui`, `--web-ui-port 8080`) is shown alongside the basic snippet.
3. All other README content (installation options, other client configs, usage, etc.) remains intact and in a logical order.
4. No broken markdown links, formatting issues, or content loss.
5. The Configuration > Cursor section no longer duplicates the uvx snippets that were moved up (but retains manual / venv options).

## Plan

### Phase A: Extract and Relocate

1. **Create a new section** between "Quick Start > Prerequisites / Python Environment" and "### Installation" titled something like "### Cursor Quick Setup (Recommended)" or similar.
2. **Move** the two Cursor uvx snippets (basic + Web UI) into this new section, with brief instructions to paste into `~/.cursor/mcp.json`.
3. **Remove** the "Using uvx (Recommended)" and "Using uvx with Web UI" entries from the Configuration > Cursor subsection to avoid duplication.
4. **Add a note** in Configuration > Cursor referencing the Quick Setup section above for uvx users.

### Phase B: Validate

1. Review the entire README top-to-bottom for logical flow.
2. Check that no markdown anchors or cross-references are broken.
3. Run quality gates (pytest, ruff, mypy) to ensure no code was accidentally affected.

## Affected Files

- `README.md` — section reorder

## Notes

- No code changes required; documentation-only task.
- Other client configurations (Claude Code, Codex CLI, Zed, Kimi) stay in the Configuration section unchanged.
- The full Cursor subsection (manual install, venv options) remains in Configuration for users who need it.

---
**Archived:** 2026-02-12
**Verdict:** PASS
