# P1-T10 Validation Report

**Task:** Document Xcode first-approval timing race in Troubleshooting & Known Issues
**Date:** 2026-03-06
**Verdict:** PASS

## Acceptance Criteria Checklist

- [x] `docs/troubleshooting.md` contains a new section for the Xcode first-approval timing race
  - Section added after "Found 0 tools" section: "MCP client shows 0 tools (green dot) after first broker connection"
  - Includes: symptom, root cause, per-process identity note, broker log signature, correct first-time setup sequence, recovery steps for Zed / Cursor / Claude Code, diagnostic command

- [x] The new section includes recovery steps for at least Zed and Cursor
  - Zed: disable → save → enable → save
  - Cursor: toggle off/on or restart
  - Claude Code: remove and re-add MCP server

- [x] `README.md` Known Issues entry expanded with client-caching consequence and link to troubleshooting section
  - Old: brief one-line description
  - New: includes "caches it permanently", green dot symptom, per-process identity note, link to docs/troubleshooting.md#mcp-client-shows-0-tools-green-dot-after-first-broker-connection

- [x] DocC `Troubleshooting.md` mirrors the new section
  - Section added: "Broker first connection: 0 tools with green connected indicator"
  - Uses DocC-compatible heading style (##)

- [x] No existing documentation removed or broken
  - All previous sections preserved; new sections inserted only

- [x] All links reference correct anchors (GitHub auto-generates anchors from headings)

## Quality Gates

- No code changes → `make test`, `make lint`, `make typecheck` not applicable
- Documentation change only — no Python source modified

## Files Modified

| File | Change |
|------|--------|
| `docs/troubleshooting.md` | Added new section (~70 lines) after "Found 0 tools" |
| `README.md` | Expanded Known Issues bullet for broker cold-start |
| `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` | Added mirrored section (~45 lines) |

## Notes

The README Known Issues entry (line 618) already had a brief mention of the Xcode approval
dialog. P1-T10 expanded it to document the client-caching consequence, green-dot symptom,
per-process identity behavior, and linked to the full troubleshooting guide.

P4-T2 (Cache tools/list in broker + upstream readiness gate) is the code-level fix for this
race condition and remains open for a future sprint.
