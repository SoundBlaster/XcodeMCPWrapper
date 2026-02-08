# Installation

Detailed installation instructions for xcodemcpwrapper.

## Installation Methods

### Method 1: Using uvx (Recommended - Easiest)

The fastest way to install is using [uvx](https://github.com/astral-sh/uv) (requires `uv` to be installed):

```bash
# No manual installation needed - uvx downloads and runs automatically
uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

uvx will automatically:
- Download the package from PyPI
- Cache it locally
- Run it without polluting your global Python environment

**Configure your MCP client with uvx** (see client-specific setup guides).

### Method 2: Using pip

```bash
pip install mcpbridge-wrapper
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/SoundBlaster/XcodeMCPWrapper.git
```

This installs the package and creates the `mcpbridge-wrapper` or `xcodemcpwrapper` command in your PATH.

### Method 3: Using the Install Script

```bash
./scripts/install.sh
```

This script will:
1. Create `~/bin/` if it doesn't exist
2. Copy the wrapper executable to `~/bin/xcodemcpwrapper`
3. Make it executable

### Method 4: Manual Installation

```bash
# Create destination directory
mkdir -p ~/bin

# Copy and make executable
cp src/mcpbridge_wrapper/cli.py ~/bin/xcodemcpwrapper
chmod +x ~/bin/xcodemcpwrapper
```

## Verify Installation

### If using uvx:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --help
```

### If using pip:

```bash
mcpbridge-wrapper --help
```

### If using manual installation:

```bash
~/bin/xcodemcpwrapper --help
```

## Uninstallation

### uvx method:

uvx caches packages automatically. To clean the cache:

```bash
uv cache clean mcpbridge-wrapper
```

### pip method:

```bash
pip uninstall mcpbridge-wrapper
```

### Manual installation:

```bash
./scripts/uninstall.sh
```

Or manually:

```bash
rm ~/bin/xcodemcpwrapper
```

## Requirements

- macOS 10.15+
- Python 3.7+
- Xcode 26.3+
- Xcode Tools MCP Server enabled in Xcode Settings

## Troubleshooting

**"command not found: uvx"**

Install uv (which includes uvx):

```bash
# Using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv
```

After installation, restart your terminal or reload your shell configuration.
