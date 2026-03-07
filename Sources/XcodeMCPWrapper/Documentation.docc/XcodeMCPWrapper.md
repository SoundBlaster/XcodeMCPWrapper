# ``XcodeMCPWrapper``

A Python wrapper that enables external AI agents to connect to Xcode via the
Model Context Protocol (MCP).

## Source Code

[https://github.com/SoundBlaster/XcodeMCPWrapper](https://github.com/SoundBlaster/XcodeMCPWrapper)

<!-- version-badge:start -->
[![Version](https://img.shields.io/badge/version-0.4.2-blue.svg)](https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.4.2)
<!-- version-badge:end -->

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

**Broker mode (Recommended):**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper", "--broker"]
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
        "--broker",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.mcpbridge_wrapper/webui.json"
      ]
    }
  }
}
```

**Direct mode (Alternative):**

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

### Broker Mode

Broker mode lets short-lived MCP sessions share one persistent upstream bridge.

- **Why this mode exists:** Apple documents a Coding Intelligence known issue in Xcode 26.4 where external development tools may trigger repeated "Allow Connection?" dialogs during normal usage (`170721057`). Reusing one long-lived upstream session via broker mode can reduce reconnect churn that surfaces this prompt pattern. See Apple's official [Xcode 26.4 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes).
- `--broker`: auto-detect — connect if daemon is alive, spawn otherwise (recommended).
- Add `--web-ui` (plus optional `--web-ui-config`) when you want the spawned or daemon host to own one shared dashboard endpoint.

Quick migration examples:

```bash
# Claude Code
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker

# Codex CLI
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

For troubleshooting and rollback details, see <doc:CursorSetup>,
<doc:ClaudeCodeSetup>, <doc:CodexCLISetup>, and <doc:Troubleshooting>.

#### Multi-Agent Guidance

When you run multiple MCP client processes at the same time:

- **Dedicated host frontend workflow (recommended when visibility matters):** start one `--broker-daemon --web-ui` process, keep every editor/client on `--broker`, and attach the browser dashboard and/or `mcpbridge-wrapper --tui` to the same host.
- **Unified single-config auto-spawn:** configure each client with `--broker --web-ui --web-ui-config <shared-path>` when you want less setup and can accept implicit host ownership.
- **Runtime expectation:** a dedicated host is the clearest way to control lifecycle; in unified auto-spawn, the first client that must spawn the broker starts the broker host and dashboard and later clients reuse it.
- **Ownership rule:** only one process can bind a given Web UI `host:port` (for example `127.0.0.1:8080`).
- **Connection behavior:** when a broker is already running, `--broker` reuses it and does not retrofit dashboard settings onto that existing host.
- **Fallback behavior:** if dashboard bind fails (port already in use), broker MCP transport continues and only dashboard startup is skipped.
- **Verification flow:** use `mcpbridge-wrapper --broker-status`, the files under `~/.mcpbridge_wrapper/`, and the shared dashboard/TUI state to verify that both editors are attached to one daemon.

See <doc:WebUIDashboard>, <doc:Troubleshooting>, <doc:CursorSetup>,
<doc:ClaudeCodeSetup>, and <doc:CodexCLISetup>.

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

Broker setup examples are listed first.

**Using uvx in broker mode (Recommended):**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper", "--broker"]
    }
  }
}
```

**Using uvx in broker mode with Web UI (Optional):**
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--broker",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.mcpbridge_wrapper/webui.json"
      ]
    }
  }
}
```

**Using uvx in direct mode:**
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

**Using uvx in direct mode with Web UI (Optional):**
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

**Using manual installation (Direct mode):**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
    }
  }
}
```

**Using manual installation with Web UI (Direct mode, optional):**
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

**Using local development (venv, direct mode):**
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper"
    }
  }
}
```

**Using local development with Web UI (Direct mode, optional):**
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper",
      "args": ["--web-ui", "--web-ui-port", "8080"]
    }
  }
}
```

#### Claude Code

Broker setup examples are listed first.

**Using uvx in broker mode (Recommended):**

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

**Using uvx in broker mode with Web UI (Optional):**
```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
```

**Using uvx in direct mode:**
```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

**Using uvx in direct mode with Web UI (Optional):**
```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

**Using manual installation (Direct mode):**

```bash
claude mcp add --transport stdio xcode -- ~/bin/xcodemcpwrapper
```

**Using manual installation with Web UI (Direct mode, optional):**
Requires installing with `./scripts/install.sh --webui` (or equivalent `.[webui]` dependencies).
```bash
claude mcp add --transport stdio xcode -- ~/bin/xcodemcpwrapper --web-ui --web-ui-port 8080
```

**Using local development (venv, direct mode):**
```bash
claude mcp add --transport stdio xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

**Using local development with Web UI (Direct mode, optional):**
```bash
claude mcp add --transport stdio xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
```

#### Codex CLI

Broker setup examples are listed first.

**Using uvx in broker mode (Recommended):**

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

**Using uvx in broker mode with Web UI (Optional):**
```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
```

**Using uvx in direct mode:**
```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

**Using uvx in direct mode with Web UI (Optional):**
```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

**Using manual installation (Direct mode):**

```bash
codex mcp add xcode -- ~/bin/xcodemcpwrapper
```

**Using manual installation with Web UI (Direct mode, optional):**
Requires installing with `./scripts/install.sh --webui` (or equivalent `.[webui]` dependencies).
```bash
codex mcp add xcode -- ~/bin/xcodemcpwrapper --web-ui --web-ui-port 8080
```

**Using local development (venv, direct mode):**
```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

**Using local development with Web UI (Direct mode, optional):**
```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
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
- For the explicit operator workflow, run one dedicated broker host with `--broker-daemon --web-ui`, then monitor that same host from the browser dashboard and/or `mcpbridge-wrapper --tui`.

## Known Issues

- **Broker cold-start — Xcode approval timing race (0 tools with green dot):** When the broker daemon starts a new `xcrun mcpbridge` process (on first launch or after a daemon restart), Xcode shows a per-process "Allow Connection?" dialog. If your MCP client sends `tools/list` *before* Xcode grants approval, it receives an empty list and **caches it permanently** — showing 0 tools with a green connected indicator and no error message. Each unique binary path (direct wrapper vs broker daemon) triggers a *separate* dialog. After approval the permission persists — no re-approval is needed on subsequent sessions. **Workaround:** watch for the Xcode dialog immediately after enabling broker mode; after clicking Allow, reload the MCP connection in your client (disable → re-enable in settings). See <doc:Troubleshooting> for client-specific recovery steps and the diagnostic command.
- **BUG-T5 → FU-P13-T7 (P0):** Empty-content tool results can still violate strict `structuredContent` expectations in strict MCP clients.
- **BUG-T6 → FU-P13-T8 (P0):** Web UI port collisions can happen when multiple MCP sessions start with the same `--web-ui-port` (for example `8080`), producing `address already in use`.
- **BUG-T7 → FU-P13-T9 (P0):** `resources/list` and `resources/templates/list` probing may return non-standard error shapes in some client paths.

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

<!-- coverage-sync: keep README and DocC coverage metrics aligned -->

| Metric | Value |
|--------|-------|
| Test Coverage | 91.62% |
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
