# Cursor Configuration Guide

## Prerequisites

- Cursor editor installed
- Xcode 26.3+ with Xcode Tools MCP enabled
- The wrapper installed (via uvx, pip, or manual)

## GUI Setup (Using uvx - Recommended)

1. Open **Cursor Settings** (`⌘,`)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter settings:
   - **Name:** `xcode-tools`
   - **Command:** `uvx`
   - **Args:** `--from mcpbridge-wrapper mcpbridge-wrapper`

## JSON Configuration

### Using uvx (Recommended)

Edit `~/.cursor/mcp.json` directly:

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

### Using uvx with Web UI (Optional)

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

### Using uvx in Broker Mode (Recommended)

`--broker` auto-detects: connects if a daemon is running, spawns one otherwise. Stale socket/PID files from a crashed daemon are cleaned up automatically.

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper",
        "mcpbridge-wrapper",
        "--broker"
      ]
    }
  }
}
```

If you manage a dedicated host with `--broker-daemon`, keep client args on
`--broker`: clients will attach when the host is alive and auto-recover by
spawning when it is not.

### Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
    }
  }
}
```

### Using Manual Installation with Web UI (Optional)

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

Replace `YOUR_USERNAME` with your actual macOS username.

### Using Local Development (venv)

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

## Migration and Rollback

- Migration to broker mode: add `--broker` to your existing `args`, then restart Cursor.
- Rollback to direct mode: remove broker flags from `args` and restart Cursor.
- After rollback, stop stale broker state files if needed:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi; rm -f "$PID_FILE" "$SOCK"
```

See [Broker Mode Guide](broker-mode.md) for full start/stop/status flows.

## Verification

1. Open Cursor
2. Start a new chat
3. You should see the Xcode tools available in the tool palette
4. Try asking "List my open Xcode windows"

## Troubleshooting

### "Tool has output schema but did not return structured content"

This error means you're connecting directly to `xcrun mcpbridge` without the wrapper. Ensure your MCP client is configured to use the wrapper command (uvx or xcodemcpwrapper), not `xcrun mcpbridge` directly.

### "command not found: uvx"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

Then restart Cursor.

### "Found 0 tools"

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON
4. Restart Cursor

### "Could not connect to broker socket ... within 10.0s"

Broker mode could not reach a ready broker socket. If using `--broker`, it will have already attempted stale-file recovery; confirm the broker process state with the [broker mode guide](broker-mode.md). To rollback, remove broker flags from `args` and restart Cursor.

### Web UI still shows old behavior after an upgrade

If Cursor is configured with Web UI args and behavior looks stale after upgrading, force a one-time uvx refresh:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--refresh",
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

Restart Cursor after saving config. Once verified, you can remove `--refresh` from args.
