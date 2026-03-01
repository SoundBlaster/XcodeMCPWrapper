# XcodeMCPWrapper - mcpbridge-wrapper

<!-- mcp-name: io.github.SoundBlaster/xcode-mcpbridge-wrapper -->

<!-- version-badge:start -->
[![Version](https://img.shields.io/badge/version-0.3.3-blue.svg)](https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.3.3)
<!-- version-badge:end -->
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-92.19%25-brightgreen.svg)](./SPECS/ARCHIVE/P5-T14_Code_Coverage/)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.SoundBlaster%2Fxcode--mcpbridge--wrapper-blue)](https://registry.modelcontextprotocol.io)

Version badge maintenance: run `make badge-version` (or `make badge-version-check` in CI).

A Python wrapper that makes Xcode 26.3's MCP bridge compatible with Cursor and other strict MCP-spec-compliant clients.

## The Problem

Xcode's `mcpbridge` returns tool responses in the `content` field but omits the required `structuredContent` field when a tool declares an `outputSchema`. According to the MCP specification, when `outputSchema` is declared, responses **must** include `structuredContent`.

- ✅ Claude Code and Codex CLI work (they have special handling for Apple's responses)
- ❌ Cursor strictly follows the spec and rejects non-compliant responses

## The Solution

`mcpbridge-wrapper` intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge-wrapper│ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Quick Start

### Prerequisites

- macOS with Xcode 26.3+
- Python 3.9+
- **Xcode Tools MCP Server enabled** (see below)

> ⚠️ **Important:** You MUST enable Xcode Tools MCP in Xcode settings:
> 1. Open **Xcode** > **Settings** (⌘,)
> 2. Select **Intelligence** in the sidebar
> 3. Under **Model Context Protocol**, toggle **Xcode Tools** ON
>
> If you see "Found 0 tools" in your MCP client logs, this setting is not enabled.

### Cursor Quick Setup

If you use **Cursor**, no installation is needed — just add this to `~/.cursor/mcp.json`:

**Broker mode (Recommended):**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper", "--broker-spawn"]
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
        "--broker-spawn",
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

Broker mode lets multiple short-lived MCP client sessions share one persistent
upstream bridge session.

- **Why this mode exists:** Apple documents a Coding Intelligence known issue in Xcode 26.4 where external development tools may trigger repeated "Allow Connection?" dialogs during normal usage (`170721057`). Reusing one long-lived upstream session via broker mode can reduce reconnect churn that surfaces this prompt pattern. See Apple's official [Xcode 26.4 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes).
- Use `--broker-connect` to attach to an already-running broker.
- Use `--broker-spawn` to auto-start the broker if needed.
- Add `--web-ui` (plus optional `--web-ui-config`) when you want the spawned or daemon host to own one shared dashboard endpoint.

Quick migration examples:

```bash
# Claude Code
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect

# Codex CLI
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect
```

For full start/stop/status commands, Cursor JSON snippets, troubleshooting, and
rollback to direct mode, see [Broker Mode Guide](docs/broker-mode.md).

#### Multi-Agent Guidance

When you run multiple MCP client processes at the same time:

- **Unified single-config pattern:** configure each client with `--broker-spawn --web-ui --web-ui-config <shared-path>`.
- **Runtime expectation:** the first client that must spawn the broker starts the broker host and dashboard; later clients reuse the same broker and dashboard endpoint.
- **Ownership rule:** only one process can bind a given Web UI `host:port` (for example `127.0.0.1:8080`).
- **Connect-only behavior:** `--broker-connect` clients never start the dashboard by themselves.
- **Fallback behavior:** if dashboard bind fails (port already in use), broker MCP transport continues and only dashboard startup is skipped.

See [Web UI Setup Guide](docs/webui-setup.md#multi-agent-web-ui-ownership-model) and [Troubleshooting](docs/troubleshooting.md#mcp-tools-are-green-but-dashboard-is-unreachable).

### Python Environment Setup (Development)

If you plan to run `make install`, `pytest`, or other development commands, create and activate a virtual environment first. This avoids Homebrew Python's `externally-managed-environment` (PEP 668) error.

```bash
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
make install
```

Quick checks:

```bash
which python3
which pip
```

Both should point to `.venv/bin/...` while the environment is active.

### Installation

#### Option 1: Using uvx (Recommended - Easiest)

The fastest way to install is using [uvx](https://github.com/astral-sh/uv) (requires `uv` to be installed):

```bash
# No manual installation needed - uvx will automatically download and run
uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

Or add to your MCP client configuration directly (see configuration sections below).

#### Option 2: Via MCP Registry

If your MCP client supports the MCP Registry:

**Server name:** `io.github.SoundBlaster/xcode-mcpbridge-wrapper`

```bash
# Using mcp-publisher CLI
mcp-publisher install io.github.SoundBlaster/xcode-mcpbridge-wrapper
```

#### Option 3: Using pip

```bash
python3 -m pip install mcpbridge-wrapper
```

Then use `mcpbridge-wrapper` or `xcodemcpwrapper` command.

#### Option 4: Manual Installation (via install script)

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
./scripts/install.sh
```

The install script creates a virtual environment, installs the package, and places a wrapper at `~/bin/xcodemcpwrapper`.

If you plan to use `--web-ui` MCP args, install Web UI extras explicitly:

```bash
./scripts/install.sh --webui
```

Add the following to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/bin:$PATH"
```

Then reload:
```bash
source ~/.zshrc
# or
. ~/.zshrc
```

#### Option 5: Local Development (venv)

For development or if you want to run directly from the cloned repository:

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
make install          # or: make install-webui (for Web UI support)
```

The entry point is `.venv/bin/mcpbridge-wrapper`. Use the **full absolute path** when configuring MCP clients (see configuration sections below).

### Uninstallation

To remove xcodemcpwrapper from your system:

```bash
./scripts/uninstall.sh
```

Options:
- `--dry-run` or `-n`: Show what would be removed without removing
- `--yes` or `-y`: Skip confirmation prompt

### Configuration

#### Cursor

Broker setup examples are listed first.

**Using uvx in broker mode (Recommended):**

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper", "--broker-spawn"]
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
        "--broker-spawn",
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
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
      "args": []
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
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-spawn
```

**Using uvx in broker mode with Web UI (Optional):**
```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker-spawn --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
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
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-spawn
```

**Using uvx in broker mode with Web UI (Optional):**
```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker-spawn --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
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

#### Zed Agent

**Using uvx (Recommended):**

Edit `~/.zed/settings.json`:

```json
{
  "xcode-tools": {
    "command": "uvx",
    "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper"],
    "env": {}
  }
}
```

**Using uvx with Web UI (Optional):**
```json
{
  "xcode-tools": {
    "command": "uvx",
    "args": [
      "--from",
      "mcpbridge-wrapper[webui]",
      "mcpbridge-wrapper",
      "--web-ui",
      "--web-ui-port",
      "8080"
    ],
    "env": {}
  }
}
```

**Using manual installation:**

```json
{
  "xcode-tools": {
    "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
    "args": [],
    "env": {}
  }
}
```

**Using manual installation with Web UI (Optional):**
Requires installing with `./scripts/install.sh --webui` (or equivalent `.[webui]` dependencies).
```json
{
  "xcode-tools": {
    "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
    "args": ["--web-ui", "--web-ui-port", "8080"],
    "env": {}
  }
}
```

**Using local development (venv, direct mode):**
```json
{
  "xcode-tools": {
    "command": "/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper",
    "args": [],
    "env": {}
  }
}
```

**Using local development with Web UI (Direct mode, optional):**
```json
{
  "xcode-tools": {
    "command": "/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper",
    "args": ["--web-ui", "--web-ui-port", "8080"],
    "env": {}
  }
}
```

#### Kimi CLI

**Using uvx (Recommended):**

Edit `~/.kimi/mcp.json`:

```json
{
  "xcode-tools": {
    "command": "uvx",
    "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper"],
    "env": {}
  }
}
```

**Using manual installation:**

```json
{
  "xcode-tools": {
    "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
    "args": [],
    "env": {}
  }
}
```

## Usage

Once configured, ask your AI assistant to use Xcode tools:

```
"Build my project"
"Run the tests"
"Find all Swift files in the project"
"Show me the build errors"
```

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

See [Web UI Setup Guide](docs/webui-setup.md) for detailed configuration.

## Known Issues

- **Broker cold-start — first use requires Xcode approval:** When the broker daemon starts a new `xcrun mcpbridge` process (on first launch or after a daemon restart), Xcode shows an "Allow Connection?" dialog. Until you click **Allow**, `tools/list` is pending and MCP clients will show 0 tools. After approval the permission persists for that binary path — no re-approval is needed on subsequent sessions. **Workaround:** watch for the Xcode dialog after enabling broker mode; if the client still shows 0 tools, toggle the MCP switch off and back on after clicking Allow.
- **BUG-T5 → FU-P13-T7 (P0):** Empty-content tool results can still violate strict `structuredContent` expectations in strict MCP clients.
- **BUG-T6 → FU-P13-T8 (P0):** Web UI port collisions can happen when multiple MCP sessions start with the same `--web-ui-port` (for example `8080`), producing `address already in use`.
- **BUG-T7 → FU-P13-T9 (P0):** `resources/list` and `resources/templates/list` probing may return non-standard error shapes in some client paths.

### Disclaimer (Codex App)

`mcpbridge-wrapper` normalizes Xcode MCP responses, but it does not control Codex App internals. Codex App transport/session behavior may change independently from Codex CLI and from this wrapper. If App and CLI differ, treat that as client-specific behavior first and verify with exact versions, config, and logs.

## Documentation

- [Installation Guide](docs/installation.md)
- [Broker Mode Guide](docs/broker-mode.md) - Configuration, migration, rollback, and operations
- [Web UI Dashboard](docs/webui-setup.md) - Real-time monitoring and audit logging
- [Cursor Setup](docs/cursor-setup.md)
- [Claude Code Setup](docs/claude-setup.md)
- [Codex CLI Setup](docs/codex-setup.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Tools Reference](docs/tools-reference.md)
- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md) - Development guide and quality gates

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

Quick quality gate check:

```bash
make test      # Run tests with coverage
make lint      # Run ruff linter
make typecheck # Run mypy type checker
```

Or run all gates:

```bash
make test && make lint && make typecheck
```

## Performance

- **Overhead:** <0.01ms per transformation
- **Memory:** <10MB footprint
- **Coverage:** 92.19% test coverage

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Apple's Xcode team for the MCP bridge functionality
- The MCP protocol specification
- The Cursor, Claude, and Codex teams for AI-powered development tools
