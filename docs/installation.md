# Installation Guide

## Prerequisites

- **macOS** with Xcode 26.3 or later installed
- **Python 3.7** or later
- **Xcode Tools MCP Server** enabled

## Step 0: Prepare Python Environment (For Development Commands)

If you will run `make install`, `make test`, or editable installs, use a virtual environment first.

```bash
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Verify the active interpreter:

```bash
which python3
which pip
```

Both should resolve to `.venv/bin/...`.

> Why this matters: macOS/Homebrew Python may block global installs with `externally-managed-environment` (PEP 668). A virtual environment is the supported fix.

## Step 1: Install Xcode 26.3+

1. Download Xcode 26.3 or later from the Mac App Store or Apple Developer Portal
2. Install and open Xcode
3. Open **Xcode > Settings** (`⌘,`)
4. Select **Intelligence** in the sidebar
5. Under **Model Context Protocol**, toggle **Xcode Tools** on

## Step 2: Install xcodemcpwrapper

### Option A: Using uvx (Recommended - Easiest)

The fastest and easiest way to install is using [uvx](https://github.com/astral-sh/uv), which is included with `uv` (the modern Python package manager).

**You don't need to manually install anything** - just configure your MCP client with the uvx command:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

uvx will automatically:
- Download the package from PyPI
- Cache it locally
- Run it without polluting your global Python environment

**Configure your MCP client (see client-specific guides):**
- [Cursor Setup](cursor-setup.md)
- [Claude Code Setup](claude-setup.md)
- [Codex CLI Setup](codex-setup.md)

### Option B: Via MCP Registry

xcodemcpwrapper is published to the [MCP Registry](https://registry.modelcontextprotocol.io).

**Registry name:** `io.github.SoundBlaster/xcode-mcpbridge-wrapper`

If your MCP client supports registry installs:

```bash
# Using mcp-publisher CLI
mcp-publisher install io.github.SoundBlaster/xcode-mcpbridge-wrapper
```

Or search for "Xcode MCP Bridge Wrapper" in your MCP client's registry browser.

### Option C: Using pip

If you prefer a traditional pip installation:

```bash
python3 -m pip install mcpbridge-wrapper
```

Or install directly from GitHub:

```bash
python3 -m pip install git+https://github.com/SoundBlaster/XcodeMCPWrapper.git
```

After pip installation, the command `mcpbridge-wrapper` or `xcodemcpwrapper` will be available.

### Option D: Manual Installation (via install script)

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
./scripts/install.sh
```

If you need Web UI support for `--web-ui` args, install with:

```bash
./scripts/install.sh --webui
```

This will:
- Create a virtual environment (`.venv`) if not already active
- Install the package into the venv
- Create `~/bin/xcodemcpwrapper` wrapper with the correct Python interpreter
- Make `xcodemcpwrapper` available in your PATH

Default `./scripts/install.sh` is base-only (no Web UI extras).

Add the following to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/bin:$PATH"
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Option E: Local Development (venv)

For development or if you want to run directly from the cloned repository:

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
make install          # or: make install-webui (for Web UI support)
```

The entry point will be at `.venv/bin/mcpbridge-wrapper`. Use the **full absolute path** when configuring MCP clients:

```bash
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

With Web UI:

```bash
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
```

## Step 3: Verify Installation

### If using uvx:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --help
```

### If using pip:

```bash
which mcpbridge-wrapper
mcpbridge-wrapper --help
```

### If using install script:

```bash
which xcodemcpwrapper
xcodemcpwrapper --help
```

### If using local development (venv):

```bash
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --help
```

You should see the help output.

## Step 4: Configure Your MCP Client

See the configuration guides for:
- [Cursor Setup](cursor-setup.md)
- [Claude Code Setup](claude-setup.md)
- [Codex CLI Setup](codex-setup.md)

## Troubleshooting

If you encounter issues during installation, see [Troubleshooting](troubleshooting.md).

### Common Issues

**"command not found: uvx"**

Install uv (which includes uvx):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

**"Found 0 tools" in MCP client**

This means Xcode Tools MCP is not enabled. See Step 1 above.
