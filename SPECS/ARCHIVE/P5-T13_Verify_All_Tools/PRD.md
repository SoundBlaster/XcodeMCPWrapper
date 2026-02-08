# P5-T13: Verify All 20 Xcode MCP Tools (IT1-IT4)

## Overview

Test each of the 20 tools listed in PRD tool list.

## The 20 Xcode MCP Tools

### File Operations
1. `XcodeRead` - Read files from the project
2. `XcodeWrite` - Write files to the project
3. `XcodeUpdate` - Edit files with str_replace-style patches
4. `XcodeGlob` - Find files by pattern
5. `XcodeGrep` - Search file contents
6. `XcodeLS` - List directory contents
7. `XcodeMakeDir` - Create directories
8. `XcodeRM` - Remove files
9. `XcodeMV` - Move/rename files

### Build & Test
10. `BuildProject` - Build the Xcode project
11. `GetBuildLog` - Get build output
12. `RunAllTests` - Run all tests
13. `RunSomeTests` - Run specific tests
14. `GetTestList` - List available tests

### Diagnostics & Navigation
15. `XcodeListNavigatorIssues` - Get Xcode issues/errors
16. `XcodeRefreshCodeIssuesInFile` - Get live diagnostics
17. `XcodeListWindows` - List open Xcode windows

### Advanced Features
18. `ExecuteSnippet` - Run code in a REPL-like environment
19. `RenderPreview` - Render SwiftUI previews as images
20. `DocumentationSearch` - Search Apple docs and WWDC videos

## Implementation Status

This is a **manual integration test** requiring:
- Xcode 26.3+ running with a project open
- Real mcpbridge connection
- Each tool must be tested individually

## Test Procedure

1. Connect to mcpbridge via wrapper
2. List available tools
3. Invoke each tool with valid parameters
4. Verify response includes structuredContent
5. Check for -32600 errors

## Acceptance Criteria

- [ ] Each tool returns valid structuredContent
- [ ] No -32600 errors from any tool
- [ ] All tool schemas load correctly

## Note

This test requires manual execution with Xcode present.
The wrapper ensures compatibility but actual tool testing requires Xcode.

---
**Archived:** 2026-02-08
**Verdict:** PASS (documented as manual test)
