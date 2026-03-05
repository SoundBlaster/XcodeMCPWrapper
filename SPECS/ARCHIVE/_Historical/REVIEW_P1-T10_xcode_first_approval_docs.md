# REVIEW: P1-T10 — Xcode First-Approval Timing Race Documentation

**Date:** 2026-03-06
**Reviewer:** Claude (automated review)
**Subject:** P1-T10 documentation deliverables

## Scope

Review of three documentation files modified in P1-T10:
- `docs/troubleshooting.md` — new section added
- `README.md` — Known Issues entry expanded
- `Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md` — new section mirrored

## Findings

### docs/troubleshooting.md

**Section title:** "MCP client shows 0 tools (green dot) after first broker connection"

Strengths:
- Symptom is clearly stated with visual cue (green dot) that users will recognize
- Root cause correctly attributes both Xcode approval dialog AND client-side caching
- Per-process identity note (direct wrapper vs broker daemon) is present and accurate
- Broker log signature (`Upstream EOF detected`) gives users a concrete diagnostic anchor
- First-time setup sequence is actionable and correctly orders: start → watch → approve → reload
- Caution note prevents pre-approval tool calls that would trigger the caching problem
- Recovery steps cover Zed, Cursor, and Claude Code specifically

No actionable issues found.

### README.md Known Issues

**Expanded entry at line 618**

Strengths:
- Now mentions "caches it permanently" — the key consequence that was missing before
- "green connected indicator" symptom is explicitly named
- Per-process identity note added
- Deep link to troubleshooting section provided

Observation: The anchor `#mcp-client-shows-0-tools-green-dot-after-first-broker-connection`
depends on GitHub's heading-to-anchor auto-generation. The heading in troubleshooting.md is:
`### "MCP client shows 0 tools (green dot) after first broker connection"`
GitHub strips quotes and special characters from anchors. The generated anchor will be:
`#mcp-client-shows-0-tools-green-dot-after-first-broker-connection`
This matches — link is correct.

No actionable issues found.

### DocC Troubleshooting.md

**Section title:** "Broker first connection: 0 tools with green connected indicator"

Strengths:
- Matches content of docs/troubleshooting.md at appropriate DocC conciseness level
- Uses `##` heading style consistent with surrounding DocC sections
- Includes per-process identity note, broker log signature, setup sequence, recovery steps
- Uses DocC-compatible bash code blocks

Observation: The section title differs slightly from `docs/troubleshooting.md`
("Broker first connection: 0 tools with green connected indicator" vs
"MCP client shows 0 tools (green dot) after first broker connection").
This is acceptable — DocC headings use a slightly different style convention (no quotes,
shorter form) and both titles clearly describe the same symptom.

No actionable issues found.

## Overall Assessment

**Verdict: PASS — No actionable findings**

All three deliverables meet the acceptance criteria from the PRD. The documentation is
accurate, covers the correct root cause discovered during live testing (client-caching +
per-process Xcode approval), and provides recovery steps for all major MCP clients.

FOLLOW-UP: Skipped — no actionable findings.
