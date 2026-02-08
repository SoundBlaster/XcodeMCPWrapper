# Configuration

Configuration options for mcpbridge-wrapper and MCP clients.

## MCP Client Configuration

### Cursor

Edit `~/.cursor/mcp.json`:

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

### Claude Code

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

Verify with:
```bash
claude mcp list
```

### Codex CLI

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

Verify with:
```bash
codex mcp list
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MCP_XCODE_PID` | Manually specify Xcode process ID when auto-detection fails | Optional |
| `MCP_XCODE_SESSION_ID` | UUID identifying an Xcode tool session | Optional |

To get the Xcode PID:
```bash
pgrep -x Xcode
```

## How Tools Work

Most tools require a `tabIdentifier` to specify which Xcode window to operate on. The typical flow:

1. **Open your project in Xcode first** (tools operate on whatever is open):
   ```bash
   open MyApp.xcodeproj
   # or
   open MyApp.xcworkspace
   ```

2. The agent automatically:
   - Calls `XcodeListWindows` to discover open windows
   - Gets the `tabIdentifier` (e.g., `windowtab1`) and workspace path
   - Uses that identifier in subsequent tool calls
