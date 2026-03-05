# Next Task: P1-T10 — Document Xcode first-approval timing race in Troubleshooting & Known Issues

**Priority:** P1
**Phase:** Phase 1: Documentation
**Effort:** 1–2h
**Dependencies:** None
**Status:** Selected

## Description

When broker mode is used for the first time, Xcode shows an approval dialog for the new daemon process. If an MCP client (Zed, Cursor) connects and sends `tools/list` before Xcode grants approval, it receives an empty tools list and caches it — showing 0 tools indefinitely until the user manually reloads the MCP connection. This is a real usability trap: the green dot shows "connected" but 0 tools, with no clear error. Document the root cause, the correct first-time setup sequence, and the recovery steps in `docs/troubleshooting.md` and as a Known Issue in `README.md`. Also note that each unique process identity (direct wrapper vs broker daemon) triggers a separate Xcode dialog.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
