# P6-T4: Create Cursor MCP Configuration Template

## Overview

Create `~/.cursor/mcp.json` configuration example.

## Implementation

Created `config/cursor-mcp.json`:
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/USERNAME/bin/mcpbridge-wrapper"
    }
  }
}
```

## Acceptance Criteria

- [x] JSON is valid
- [x] Path uses `$HOME` or documents username replacement

---
**Archived:** 2026-02-08
**Verdict:** PASS
