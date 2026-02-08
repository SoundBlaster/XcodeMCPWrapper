# Claude Code Configuration Guide

## Prerequisites

- Claude Code CLI installed
- Xcode 26.3+ with Xcode Tools MCP enabled

## One-Line Setup (Using uvx - Recommended)

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

## Alternative: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
```

Replace `YOUR_USERNAME` with your actual macOS username.

## Verification

```bash
claude mcp list
```

You should see `xcode` in the list of MCP servers.

## Usage

Once configured, you can use Xcode tools in Claude Code:

```
> Build my Xcode project
```

Claude will automatically use the Xcode MCP tools through the wrapper.

## Removing

To remove the MCP server:

```bash
claude mcp remove xcode
```

## Troubleshooting

### "command not found: uvx"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

### "Found 0 tools"

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON
