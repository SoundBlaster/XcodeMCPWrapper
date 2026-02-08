# Installation Guide

## Prerequisites

- **macOS** with Xcode 26.3 or later installed
- **Python 3.7** or later
- **Xcode Tools MCP Server** enabled

## Step 1: Install Xcode 26.3+

1. Download Xcode 26.3 or later from the Mac App Store or Apple Developer Portal
2. Install and open Xcode
3. Open **Xcode > Settings** (`⌘,`)
4. Select **Intelligence** in the sidebar
5. Under **Model Context Protocol**, toggle **Xcode Tools** on

## Step 2: Install mcpbridge-wrapper

### Option A: Using the install script (Recommended)

```bash
git clone https://github.com/yourusername/mcpbridge-wrapper.git
cd mcpbridge-wrapper
./scripts/install.sh
```

This will:
- Check your Python version
- Create `~/bin/` if it doesn't exist
- Install the package
- Make `mcpbridge-wrapper` available in your PATH

### Option B: Using pip

```bash
pip install git+https://github.com/yourusername/mcpbridge-wrapper.git
```

### Option C: Manual installation

```bash
git clone https://github.com/yourusername/mcpbridge-wrapper.git
cd mcpbridge-wrapper
pip install -e .
```

## Step 3: Verify Installation

```bash
which mcpbridge-wrapper
mcpbridge-wrapper --help
```

You should see the help output.

## Step 4: Configure Your MCP Client

See the configuration guides for:
- [Cursor Setup](cursor-setup.md)
- [Claude Code Setup](claude-setup.md)
- [Codex CLI Setup](codex-setup.md)

## Troubleshooting

If you encounter issues during installation, see [Troubleshooting](troubleshooting.md).
