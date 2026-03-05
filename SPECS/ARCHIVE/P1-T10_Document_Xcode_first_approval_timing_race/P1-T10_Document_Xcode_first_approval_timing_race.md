# P1-T10 — Document Xcode First-Approval Timing Race

**Task ID:** P1-T10
**Priority:** P1
**Phase:** Phase 1 — Documentation
**Status:** In Progress

## Problem Statement

When broker mode is used for the first time (or after a daemon restart), Xcode shows a per-process
"Allow Connection?" dialog for the new `mcpbridge` process. If an MCP client (Zed, Cursor, Claude Code)
connects and sends `tools/list` *before* Xcode grants approval, it receives an empty tools list and
**caches it permanently** — showing 0 tools with a green "connected" indicator and no actionable error.

The user sees:
- Green connected indicator in their MCP client
- 0 tools visible
- No error message — just silence

This is a usability trap with no obvious recovery path unless you know the root cause.

### Key Facts Discovered During Live Testing

1. **Per-process identity**: Each unique binary path triggers a separate Xcode dialog:
   - Direct wrapper (`mcpbridge-wrapper` without `--broker`) — one approval
   - Broker daemon (`mcpbridge-wrapper --broker-daemon`) — a *different* approval

2. **Client caching**: MCP clients cache the `tools/list` response. An empty list received
   during the approval window is stored and served indefinitely until the user manually
   reloads/restarts the MCP connection.

3. **Broker reconnect cycling**: During the Xcode approval dialog, the broker's upstream
   `xcrun mcpbridge` detects EOF and cycles. Logs show:
   ```
   Upstream EOF detected; scheduling reconnect
   ```
   repeated 2–3 times before Xcode approval stabilizes the connection.

4. **Recovery sequence**: After clicking Allow in Xcode, MCP clients still show 0 tools
   because they cache the old empty response. Users must manually reload the MCP connection
   (disable → re-enable in client settings).

## Deliverables

### 1. `docs/troubleshooting.md` — New Section

Add a new troubleshooting entry titled:
`"MCP client shows 0 tools (green dot) after first broker connection"`

Content must include:
- Symptom description (green dot, 0 tools, no error)
- Root cause explanation (Xcode per-process approval + client caching)
- Per-process identity note (direct mode vs broker daemon are separate approvals)
- Correct first-time setup sequence (start broker → watch for Xcode dialog → approve → then reload client)
- Client-specific recovery steps:
  - Zed: disable MCP in settings → save → enable → save, wait for spinner
  - Cursor: open MCP settings → disconnect → reconnect (or restart Cursor)
  - Claude Code: `claude mcp remove xcode && claude mcp add ...` (or session restart)
- Broker log diagnostic hint (look for `Upstream EOF detected`)

Place this section after the existing `"Found 0 tools"` section (line ~5 of troubleshooting.md)
since it is the next most common variation.

### 2. `README.md` — Expand Known Issues Entry

The existing entry (line 618) reads:
> **Broker cold-start — first use requires Xcode approval:** [brief text]

Expand it to include:
- The client-caching consequence (empty list gets cached permanently)
- The green-dot-with-0-tools symptom
- The per-process identity note
- A link to the new troubleshooting section: `[Troubleshooting: Xcode first-approval timing race](docs/troubleshooting.md#mcp-client-shows-0-tools-green-dot-after-first-broker-connection)`

### 3. `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` — Mirror

Add the same new section to the DocC troubleshooting file (mirrors `docs/troubleshooting.md`),
using DocC link syntax where needed.

## Acceptance Criteria

- [ ] `docs/troubleshooting.md` contains a new section for the Xcode first-approval timing race
- [ ] The new section includes: symptom, root cause, per-process identity note, first-time setup
      sequence, and recovery steps for at least Zed and Cursor
- [ ] `README.md` Known Issues entry for broker cold-start is expanded with client-caching
      consequence and links to the new troubleshooting section
- [ ] DocC `Troubleshooting.md` mirrors the new section
- [ ] No existing documentation is removed or broken
- [ ] All links resolve correctly

## Implementation Notes

- Insert the new troubleshooting section near the top of `docs/troubleshooting.md`, after
  the existing "Found 0 tools" section (around line 31), since it is a variant of that symptom.
- The DocC file uses `##` headings for its sections — match that style.
- The README Known Issues list uses bold key phrases followed by colon — match that style.
- Anchor for the new troubleshooting section (for deep linking from README):
  `#mcp-client-shows-0-tools-green-dot-after-first-broker-connection`

## Out of Scope

- Code changes to fix the race (tracked as P4-T2)
- Changes to broker-mode.md (that doc covers operational flows; troubleshooting lives here)
