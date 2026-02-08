# Cursor Configuration Guide

## Prerequisites

- Cursor editor installed
- Xcode 26.3+ with Xcode Tools MCP enabled
- The wrapper installed (via uvx, pip, or manual)

## GUI Setup (Using uvx - Recommended)

1. Open **Cursor Settings** (`⌘,`)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter settings:
   - **Name:** `xcode-tools`
   - **Command:** `uvx`
   - **Args:** `--from mcpbridge-wrapper mcpbridge-wrapper`

## JSON Configuration

### Using uvx (Recommended)

Edit `~/.cursor/mcp.json` directly:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper"]
    }
  }
}
```

### Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
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

### "Tool has output schema but did not return structured content"

This error means you're connecting directly to `xcrun mcpbridge` without the wrapper. Ensure your MCP client is configured to use the wrapper command (uvx or xcodemcpwrapper), not `xcrun mcpbridge` directly.

### "command not found: uvx"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

Then restart Cursor.

### "Found 0 tools"

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON
4. Restart Cursor
