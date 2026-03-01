# Codex CLI Configuration Guide

## Prerequisites

- Codex CLI installed
- Xcode 26.3+ with Xcode Tools MCP enabled

## One-Line Setup (Using uvx - Recommended)

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

## Optional: One-Line Setup with Web UI

Use this variant to enable the dashboard on port `8080`:

```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

## Optional: One-Line Setup in Broker Mode

`--broker` auto-detects: connects if a daemon is running, spawns one otherwise. Stale socket/PID files from a crashed daemon are cleaned up automatically.

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

If you run a dedicated host with `--broker-daemon`, keep clients on `--broker`
so they attach when available and auto-recover when the host is absent.

## Alternative: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
```

### Manual Installation with Web UI (Optional)

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper --web-ui --web-ui-port 8080
```

Replace `YOUR_USERNAME` with your actual macOS username.

## Local Development (from cloned repo with venv)

If you cloned the repo and installed via `make install` in a virtual environment:

```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

### Local Development with Web UI (Optional)

```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Replace `/path/to/XcodeMCPWrapper` with the actual path to your cloned repository.

## Migration and Rollback

- Migration: update the existing `codex mcp add ...` command to include `--broker`, then re-add the server.
- Rollback: remove broker flags and run `codex mcp add ...` again for direct mode.
- Stop stale broker artifacts during rollback if needed:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi; rm -f "$PID_FILE" "$SOCK"
```

See [Broker Mode Guide](broker-mode.md) for start/stop/status commands.

## Verification

```bash
codex mcp list
```

You should see `xcode` in the list of MCP servers.

## Usage

Once configured, you can use Xcode tools in Codex CLI:

```bash
codex "Run my unit tests"
```

Codex will automatically use the Xcode MCP tools through the wrapper.

## Removing

To remove the MCP server:

```bash
codex mcp remove xcode
```

## Troubleshooting

### "command not found: uvx"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

### "Found 0 tools"

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON

### "Could not connect to broker socket ... within 10.0s"

Broker mode could not reach a ready broker socket. If using `--broker`, stale files are cleaned up automatically; verify broker status from the [broker mode guide](broker-mode.md), or rollback to direct mode by removing broker flags.
