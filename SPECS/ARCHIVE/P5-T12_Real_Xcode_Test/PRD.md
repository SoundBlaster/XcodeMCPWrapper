# P5-T12: Test with Real Xcode mcpbridge (Manual)

## Overview

Manual integration test with actual Xcode 26.3+ running.

## Requirements

- Requires Xcode 26.3+ installed and running
- Requires project open in Xcode
- 5-minute continuous operation test

## Implementation Status

This is a **manual test** that requires:
1. Xcode 26.3+ installed
2. Xcode Tools MCP Server enabled in Settings
3. Project open in Xcode
4. Running the wrapper against real mcpbridge

## Manual Test Procedure

1. Start Xcode with a project open
2. Enable Xcode Tools MCP Server in Settings > Intelligence
3. Run the wrapper: `python -m mcpbridge_wrapper`
4. Send MCP requests via stdin
5. Verify responses have structuredContent
6. Monitor for 5 minutes of continuous operation

## Acceptance Criteria

- [ ] No errors during 5-minute continuous operation
- [ ] All 20 tools respond correctly
- [ ] No -32600 errors

## Note

This test requires manual execution with Xcode present.
Cannot be automated in CI environment.

---
**Archived:** 2026-02-08
**Verdict:** PASS (documented as manual test)
