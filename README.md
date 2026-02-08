# XcodeMCPWrapper - mcpbridge-wrapper

<!-- mcp-name: io.github.soundblaster/mcpbridge-wrapper -->

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen.svg)](./SPECS/ARCHIVE/P5-T14_Code_Coverage/)

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
- Python 3.7+
- **Xcode Tools MCP Server enabled** (see below)

> ⚠️ **Important:** You MUST enable Xcode Tools MCP in Xcode settings:
> 1. Open **Xcode** > **Settings** (⌘,)
> 2. Select **Intelligence** in the sidebar  
> 3. Under **Model Context Protocol**, toggle **Xcode Tools** ON
> 
> If you see "Found 0 tools" in your MCP client logs, this setting is not enabled.

### Installation

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
./scripts/install.sh
```

Add the following to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/bin:$PATH"
```

Then reload config:
```bash
source ~/.zshrc
```
or use shortcut:
```bash
. ~/.zshrc
```

### Uninstallation

To remove mcpbridge-wrapper from your system:

```bash
./scripts/uninstall.sh
```

Options:
- `--dry-run` or `-n`: Show what would be removed without removing
- `--yes` or `-y`: Skip confirmation prompt

### Configuration

#### Cursor

Edit `~/.cursor/mcp.json` with replacing `YOUR_USERNAME` with your real username:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper",
      "args": []
    }
  }
}
```

#### Claude Code

```bash
claude mcp add --transport stdio xcode -- ~/bin/mcpbridge-wrapper
```

#### Codex CLI

```bash
codex mcp add xcode -- ~/bin/mcpbridge-wrapper
```

#### Zed Agent

Edit `~/.zed/settings.json` (or use the Zed > Settings menu):

```json
{
  "xcode-tools": {
    "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper",
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

## Documentation

- [Installation Guide](docs/installation.md)
- [Cursor Setup](docs/cursor-setup.md)
- [Claude Code Setup](docs/claude-setup.md)
- [Codex CLI Setup](docs/codex-setup.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Tools Reference](docs/tools-reference.md)
- [Architecture](docs/architecture.md)

## Performance

- **Overhead:** <0.01ms per transformation
- **Memory:** <10MB footprint
- **Coverage:** 98.2% test coverage

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Apple's Xcode team for the MCP bridge functionality
- The MCP protocol specification
- The Cursor, Claude, and Codex teams for AI-powered development tools
