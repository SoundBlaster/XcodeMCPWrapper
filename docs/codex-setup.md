# Codex CLI Configuration Guide

## One-Line Setup

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
```

Replace `YOUR_USERNAME` with your actual macOS username.

## Verification

```bash
codex mcp list
```

You should see `xcode` in the list of MCP servers.

## Usage

Once configured, you can use Xcode tools in Codex CLI:

```bash
codex "Run my unit tests"
```

Codex will automatically use the Xcode MCP tools through the wrapper.

## Removing

To remove the MCP server:

```bash
codex mcp remove xcode
```
