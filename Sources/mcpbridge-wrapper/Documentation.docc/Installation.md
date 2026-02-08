# Installation

Detailed installation instructions for mcpbridge-wrapper.

## Installation Methods

### Method 1: Using the Install Script (Recommended)

```bash
./scripts/install.sh
```

This script will:
1. Create `~/bin/` if it doesn't exist
2. Copy the wrapper executable to `~/bin/mcpbridge-wrapper`
3. Make it executable

### Method 2: Using pip

```bash
pip install -e .
```

This installs the package and creates the `mcpbridge-wrapper` command in your PATH.

### Method 3: Manual Installation

```bash
# Create destination directory
mkdir -p ~/bin

# Copy and make executable
cp src/mcpbridge_wrapper/cli.py ~/bin/mcpbridge-wrapper
chmod +x ~/bin/mcpbridge-wrapper
```

## Verify Installation

```bash
# Check the wrapper is executable
~/bin/mcpbridge-wrapper --help

# Or if installed via pip
mcpbridge-wrapper --help
```

## Uninstallation

```bash
./scripts/uninstall.sh
```

Or manually:

```bash
rm ~/bin/mcpbridge-wrapper
pip uninstall mcpbridge-wrapper
```

## Requirements

- macOS 10.15+
- Python 3.7+
- Xcode 26.3+
- Xcode Tools MCP Server enabled in Xcode Settings
