# Claude Code Configuration Guide

## One-Line Setup

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
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
