# Cursor Configuration Guide

## GUI Setup

1. Open **Cursor Settings** (`⌘,`)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter settings:
   - **Name:** `xcode-tools`
   - **Command:** `/Users/YOUR_USERNAME/bin/mcpbridge-wrapper`

## JSON Configuration

Alternatively, edit `~/.cursor/mcp.json` directly:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper"
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual macOS username.

## Verification

1. Open Cursor
2. Start a new chat
3. You should see the Xcode tools available in the tool palette
4. Try asking "List my open Xcode windows"

## Troubleshooting

If you see "Tool has output schema but did not return structured content" errors, 
ensure you're using the wrapper and not calling `xcrun mcpbridge` directly.
