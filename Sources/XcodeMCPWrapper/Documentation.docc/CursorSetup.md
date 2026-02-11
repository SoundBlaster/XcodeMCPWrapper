# Cursor Setup

Configure Cursor to use Xcode MCP tools via xcodemcpwrapper.

## Prerequisites

- Cursor editor installed
- Xcode 26.3+ with Xcode Tools MCP enabled

## Configuration Steps

### Option 1: Using uvx (Recommended)

No manual installation needed. Configure Cursor directly:

1. Open **Cursor Settings** (`⌘,`)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter settings:
   - **Name:** `xcode-tools`
   - **Command:** `uvx`
   - **Args:** `--from mcpbridge-wrapper mcpbridge-wrapper`

Or edit `~/.cursor/mcp.json` directly:

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

### Option 2: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

1. Get your username:
   ```bash
   whoami
   ```

2. Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
    }
  }
}
```

Replace `YOUR_USERNAME` with the output from `whoami`.

### Option 3: Using Local Development (venv)

If you cloned the repo and installed via `make install` in a virtual environment:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper"
    }
  }
}
```

With Web UI:

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

Replace `/path/to/XcodeMCPWrapper` with the actual path to your cloned repository.

### Restart Cursor

Quit and reopen Cursor to load the new MCP configuration.

### Verify Setup

Open an Xcode project, then in Cursor ask:

> "List my open Xcode windows"

Cursor should respond with the available Xcode windows.

## Troubleshooting

**"Tool XcodeListWindows has an output schema but did not return structured content"**

This means you're not using the wrapper. Ensure:
1. The command in `mcp.json` is correct (uvx or path to xcodemcpwrapper)
2. Cursor has been restarted after configuration changes

**"command not found: uvx"**

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

Then restart Cursor.

**"Found 0 tools"**

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON
4. Restart Cursor
