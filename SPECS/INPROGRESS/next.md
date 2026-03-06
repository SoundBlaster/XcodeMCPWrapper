# Next Task: P1-T12 — Improve troubleshooting docs for Zed broker startup timeouts

**Priority:** P1
**Phase:** Phase 1: Documentation
**Effort:** 2 hours
**Dependencies:** P1-T10
**Status:** Selected

## Description

Document the Zed-specific broker startup failure path in the troubleshooting guide: after first approval the server can appear green with 0 tools, then later fail with `Context server request timeout`. Capture the working recovery sequence that uses a dedicated broker host and explain why inactive `mcpbridge-broker` rows in Xcode do not necessarily mean multiple live brokers.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
