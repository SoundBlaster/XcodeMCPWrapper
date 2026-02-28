# ``XcodeMCPWrapper``

A Python wrapper that enables external AI agents to connect to Xcode via the Model Context Protocol (MCP).

## Source Code

[https://github.com/SoundBlaster/XcodeMCPWrapper](https://github.com/SoundBlaster/XcodeMCPWrapper)

<!-- version-badge:start -->
[![Version](https://img.shields.io/badge/version-0.3.3-blue.svg)](https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.3.3)
<!-- version-badge:end -->

Version badge maintenance: run `make badge-version` (or `make badge-version-check` in CI).

## Overview

Xcode 26.3+ includes an MCP bridge (`xcrun mcpbridge`) that exposes Xcode's internal capabilities to MCP clients. However, it has a protocol compatibility issue that prevents it from working with strict MCP spec followers like Cursor.

This wrapper intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

### Key Features

- **🔧 Protocol Compatibility**: Fixes the `structuredContent` field issue that causes -32600 errors in strict MCP clients
- **⚡ Zero Configuration**: Works out of the box with uvx - no manual installation needed
- **🚀 Lightweight**: <0.01ms overhead per transformation, <10MB memory footprint
- **🔌 Universal Support**: Works with Cursor, Claude Code, Codex CLI, and any MCP-compatible client
- **📡 Transparent**: Passes through all non-tool responses unchanged

## System Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │  xcodemcpwrapper │ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Quick Start

### Prerequisites

- macOS with Xcode 26.3+
- Python 3.9+

### Cursor Quick Setup

If you use **Cursor**, no installation is needed — just add this to `~/.cursor/mcp.json`:

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

With Web UI dashboard (optional — adds real-time monitoring at http://localhost:8080):

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--web-ui",
        "--web-ui-port",
        "8080"
      ]
    }
  }
}
```

If you upgrade and want to confirm the currently running dashboard process version:

```bash
PORT=8080
PID=$(lsof -tiTCP:$PORT -sTCP:LISTEN | head -n1)
PY=$(ps -p "$PID" -o command= | awk '{print $1}')
"$PY" -c 'import importlib.metadata as m; print(m.version("mcpbridge-wrapper"))'
```

If needed, do a one-time refresh start:

```bash
uvx --refresh --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Restart Cursor and you're done. For other clients or installation methods, read on.

### Broker Mode (Optional)

Broker mode lets short-lived MCP sessions share one persistent upstream bridge.

- **Why this mode exists:** Apple documents a Coding Intelligence known issue in Xcode 26.4 where external development tools may trigger repeated "Allow Connection?" dialogs during normal usage (`170721057`). Reusing one long-lived upstream session via broker mode can reduce reconnect churn that surfaces this prompt pattern. See Apple's official [Xcode 26.4 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes).
- `--broker-connect`: attach to an already-running broker.
- `--broker-spawn`: best-effort auto-start, then connect.
- Add `--web-ui` (plus optional `--web-ui-config`) when you want the spawned or daemon host to own one shared dashboard endpoint.

Quick migration examples:

```bash
# Claude Code
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect

# Codex CLI
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect
```

For troubleshooting and rollback details, see <doc:CursorSetup>,
<doc:ClaudeCodeSetup>, <doc:CodexCLISetup>, and <doc:Troubleshooting>.

#### Multi-Agent Guidance

When you run multiple MCP client processes at the same time:

- **Unified single-config pattern:** configure each client with `--broker-spawn --web-ui --web-ui-config <shared-path>`.
- **Runtime expectation:** the first client that must spawn the broker starts the broker host and dashboard; later clients reuse the same broker and dashboard endpoint.
- **Ownership rule:** only one process can bind a given Web UI `host:port` (for example `127.0.0.1:8080`).
- **Connect-only behavior:** `--broker-connect` clients never start the dashboard by themselves.
- **Fallback behavior:** if dashboard bind fails (port already in use), broker MCP transport continues and only dashboard startup is skipped.

See <doc:WebUIDashboard> and <doc:Troubleshooting>.

### Python Environment Setup (Development)

If you plan to run development commands such as `make install`, `make test`, or editable installs, create and activate a virtual environment first. This avoids Homebrew Python's `externally-managed-environment` (PEP 668) error.

```bash
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Verify activation:

```bash
which python3
which pip
```

Both should resolve to `.venv/bin/...`.

### 1. Install the Wrapper (Using uvx - Recommended)

The easiest way is using [uvx](https://github.com/astral-sh/uv):

```bash
# No manual installation needed - uvx downloads and runs automatically
uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

Or install via pip:
```bash
python3 -m pip install mcpbridge-wrapper
```

Or manually:
```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
./scripts/install.sh
```

If you plan to use `--web-ui` MCP args with manual install:
```bash
./scripts/install.sh --webui
```

For local development from a clone:
```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
make install          # or: make install-webui (for Web UI support)
```

### Uninstallation

To remove xcodemcpwrapper from your system:

```bash
./scripts/uninstall.sh
```

### 2. Configure Your MCP Client

#### Cursor

For **uvx** setup (recommended), see **Cursor Quick Setup** above.

**Using manual installation:**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
    }
  }
}
```

**Using manual installation with Web UI (Optional):**
> Requires installing with `./scripts/install.sh --webui` (or equivalent `.[webui]` dependencies).
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
      "args": ["--web-ui", "--web-ui-port", "8080"]
    }
  }
}
```

#### Claude Code

**Using uvx (Recommended):**

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

**Using uvx with Web UI (Optional):**
```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

**Using manual installation:**

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
```

#### Codex CLI

**Using uvx (Recommended):**

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

**Using uvx with Web UI (Optional):**
```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

**Using manual installation:**

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
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

## Web UI Dashboard (Optional)

The wrapper includes an optional Web UI dashboard for real-time monitoring and audit logging:

```bash
# Start with Web UI
make webui

# Or directly
python -m mcpbridge_wrapper --web-ui --web-ui-port 8080
```

Features:
- **Real-time metrics**: RPS, latency percentiles (p50, p95, p99), error rates
- **Tool usage analytics**: Visual charts of most frequently used tools
- **Audit logging**: Persistent log of all MCP tool calls with export (JSON/CSV)
- **Request inspector**: Live log stream with filtering

Open http://localhost:8080 in your browser to view the dashboard.

Important for multi-agent setups:
- The dashboard is hosted by one wrapper process, not by Xcode or `mcpbridge`.
- A single `host:port` can have only one listener; additional processes on the same port skip dashboard startup and continue MCP traffic.

## Known Issues

- **BUG-T5 → FU-P13-T7 (P0):** Empty-content tool results can still violate strict `structuredContent` expectations in strict MCP clients.
- **BUG-T6 → FU-P13-T8 (P0):** Web UI port collisions can happen when multiple MCP sessions start with the same `--web-ui-port` (for example `8080`), producing `address already in use`.
- **BUG-T7 → FU-P13-T9 (P0):** `resources/list` and `resources/templates/list` probing may return non-standard error shapes in some client paths.
- **BUG-T3 (resolved):** If dashboard access is needed independently from MCP startup, run `--web-ui-only` for standalone diagnostics.

### Disclaimer (Codex App)

`mcpbridge-wrapper` normalizes Xcode MCP responses, but it does not control Codex App internals. Codex App transport/session behavior may change independently from Codex CLI and from this wrapper. If App and CLI differ, treat that as client-specific behavior first and verify with exact versions, config, and logs.

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
- <doc:WebUIDashboard> - Real-time monitoring and audit logging

## Project Status

**✅ COMPLETE**

| Metric | Value |
|--------|-------|
| Test Coverage | 92.19% |
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
- <doc:WebUIDashboard>
