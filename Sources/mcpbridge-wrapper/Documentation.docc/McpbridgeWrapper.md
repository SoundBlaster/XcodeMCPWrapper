# ``mcpbridge_wrapper``

A Python wrapper that enables external AI agents to connect to Xcode via the Model Context Protocol (MCP).

## Overview

Xcode 26.3+ includes an MCP bridge (`xcrun mcpbridge`) that exposes Xcode's internal capabilities to MCP clients. However, it has a protocol compatibility issue that prevents it from working with strict MCP spec followers like Cursor.

This wrapper intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

### Key Features

- **🔧 Protocol Compatibility**: Fixes the `structuredContent` field issue that causes -32600 errors in strict MCP clients
- **⚡ Zero Configuration**: Works out of the box with a simple installation
- **🚀 Lightweight**: <0.01ms overhead per transformation, <10MB memory footprint
- **🔌 Universal Support**: Works with Cursor, Claude Code, Codex CLI, and any MCP-compatible client
- **📡 Transparent**: Passes through all non-tool responses unchanged

## Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge-wrapper│ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Quick Start

### 1. Install the Wrapper

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
./scripts/install.sh
```

### 2. Configure Your MCP Client

#### Cursor

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

#### Claude Code

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

#### Codex CLI

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

### 3. Enable Xcode Tools

Open **Xcode > Settings** (`⌘,`), select **Intelligence**, and toggle **Xcode Tools** on under Model Context Protocol.

### 4. Start Using Xcode MCP Tools

Your AI agent can now use all 20 Xcode MCP tools including:

- `XcodeRead` - Read files from the project
- `XcodeWrite` - Write files to the project  
- `XcodeUpdate` - Edit files with patches
- `BuildProject` - Build the Xcode project
- `RunAllTests` - Run all tests

## Tutorials

- <doc:GettingStarted> - Get up and running in minutes
- <doc:Installation> - Detailed installation instructions
- <doc:Configuration> - Configure for different MCP clients

## Supported Clients

- <doc:CursorSetup> - Cursor editor configuration
- <doc:ClaudeCodeSetup> - Claude Code setup
- <doc:CodexCLISetup> - Codex CLI configuration

## Reference

- <doc:Troubleshooting> - Common issues and solutions
- <doc:Architecture> - How the wrapper works internally
- <doc:EnvironmentVariables> - Optional configuration options

## Project Status

**✅ COMPLETE**

| Metric | Value |
|--------|-------|
| Test Coverage | 98.2% |
| Performance Overhead | <0.01ms per transformation |
| Memory Footprint | <10MB |

## Topics

### Getting Started

- <doc:GettingStarted>
- <doc:Installation>
- <doc:Configuration>

### Supported Clients

- <doc:CursorSetup>
- <doc:ClaudeCodeSetup>
- <doc:CodexCLISetup>

### Reference

- <doc:Troubleshooting>
- <doc:Architecture>
- <doc:EnvironmentVariables>
