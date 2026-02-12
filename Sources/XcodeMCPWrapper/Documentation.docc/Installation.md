# Installation

Detailed installation instructions for xcodemcpwrapper.

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
python3 -m pip install mcpbridge-wrapper
```

Or install directly from GitHub:

```bash
python3 -m pip install git+https://github.com/SoundBlaster/XcodeMCPWrapper.git
```

This installs the package and creates the `mcpbridge-wrapper` or `xcodemcpwrapper` command in your PATH.

### Method 3: Using the Install Script

```bash
./scripts/install.sh
```

If you need Web UI support for `--web-ui` args, install with:

```bash
./scripts/install.sh --webui
```

This script will:
1. Create a virtual environment (`.venv`) if not already active
2. Install the package into the venv
3. Create `~/bin/xcodemcpwrapper` wrapper with the correct Python interpreter
4. Make it executable

Default `./scripts/install.sh` is base-only (no Web UI extras).

### Method 4: Local Development (venv)

For development or running directly from the cloned repository:

```bash
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .    # or: pip install -e ".[webui]"
```

The entry point is `.venv/bin/mcpbridge-wrapper`. Use the full absolute path when configuring MCP clients:

```bash
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
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

### If using install script:

```bash
~/bin/xcodemcpwrapper --help
```

### If using local development (venv):

```bash
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --help
```

## Uninstallation

### uvx method:

uvx caches packages automatically. To clean the cache:

```bash
uv cache clean mcpbridge-wrapper
```

### pip method:

```bash
python3 -m pip uninstall mcpbridge-wrapper
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
