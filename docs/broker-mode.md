# Broker Mode Guide

Broker mode lets short-lived MCP client processes share a single long-lived upstream
`xcrun mcpbridge` session.

## Mode summary

| Flag | Role |
|------|------|
| *(none — default)* | `direct`: each wrapper process launches its own upstream bridge. |
| `--broker-daemon` | **Daemon host**: long-lived process that owns the upstream bridge and accepts client connections on a Unix socket. Start this once, then point clients at it. |
| `--broker` | **Proxy + auto-detect** *(recommended)*: connects to a running broker if one is alive, spawns a new daemon otherwise. Automatically recovers stale socket/PID files left by a crashed daemon. |

Use broker mode when you want lower process churn across repeated MCP client restarts.

## Multi-agent topology and Web UI ownership

Recommended topology for multiple agents/clients:

1. **Unified single-config (recommended):** use the same client args everywhere:
   `--broker --web-ui --web-ui-config <shared-path>`.
2. **Dedicated host alternative:** run one explicit broker host with
   `--broker-daemon --web-ui` and configure clients with `--broker`.

Web UI behavior in broker modes:

- `--broker-daemon --web-ui` starts broker + dashboard in one host process.
- `--broker --web-ui` forwards Web UI flags to the spawned daemon when auto-start is needed; if a broker is already running without `--web-ui`, a warning is printed to stderr.
- When `--broker` reuses an already-running daemon, it does not change that daemon's dashboard state.
- Only one process can own a given Web UI `host:port`.
- If dashboard bind fails (for example port already in use), broker transport continues and only dashboard startup is skipped.

## Paths used by broker mode

By default, broker state is stored in `~/.mcpbridge_wrapper/`:

- Socket: `~/.mcpbridge_wrapper/broker.sock`
- PID file: `~/.mcpbridge_wrapper/broker.pid`
- Recommended log: `~/.mcpbridge_wrapper/broker.log`

## Operational flows

### Start (daemon host)

Start a dedicated background broker host first for predictable operation:

```bash
mkdir -p "$HOME/.mcpbridge_wrapper"
nohup mcpbridge-wrapper --broker-daemon --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json" \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
echo "Broker started (PID $!)"
```

Or using `uvx`:

```bash
nohup uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-daemon --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json" \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

Then configure MCP clients with `--broker` (see client examples below).

`--broker` is the recommended alternative that auto-detects: connects if a broker is alive, spawns otherwise (including dashboard args):

```bash
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

### Status

```bash
mcpbridge-wrapper --broker-status
```

Prints proxy version, daemon PID, daemon version, file paths, and warns on version mismatch.

### Logs

```bash
tail -f "$HOME/.mcpbridge_wrapper/broker.log"
```

### Stop

```bash
mcpbridge-wrapper --broker-stop
```

Sends SIGTERM to the running daemon, waits up to 3 seconds for a clean exit, and removes PID/socket/version files.

## Version management

When upgrading `mcpbridge-wrapper` (via `pip install`, `uvx`, or `./scripts/install.sh`):

1. The **install script** automatically stops any running broker daemon.
2. On next `--broker` launch, the proxy compares its version against the daemon's
   version file (`~/.mcpbridge_wrapper/broker.version`). If versions differ, the
   stale daemon is stopped and a fresh one is spawned automatically.
3. Use `--broker-status` to verify the running daemon matches the installed version.

If an older daemon was started before the upgrade and you want to force an immediate
restart, run `mcpbridge-wrapper --broker-stop` followed by any `--broker` command.

## Client configuration examples

### Unified single-config examples (recommended)

Use the same args in every client. The first client that needs auto-spawn starts the broker host and dashboard; later clients attach to the same host/session.

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--broker",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.config/xcodemcpwrapper/webui.json"
      ]
    }
  }
}
```

### Zed Agent (`settings.json`)

```json
{
  "context_servers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--broker",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.config/xcodemcpwrapper/webui.json"
      ],
      "env": {}
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport stdio xcode -- \
  uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

### Codex CLI

```bash
codex mcp add xcode -- \
  uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

### Dedicated host alternative

If you prefer explicit host lifecycle management, start one `--broker-daemon --web-ui` process manually and configure clients with `--broker`.

## Migration from direct mode to broker mode

1. Back up your current MCP client configuration.
2. Choose one rollout pattern:
   - Unified config: set clients to `--broker --web-ui --web-ui-config <shared-path>`.
   - Dedicated host: start `--broker-daemon --web-ui` once and set clients to `--broker`.
3. Restart each MCP client.
4. Run a first MCP request and verify broker files exist:
   - `~/.mcpbridge_wrapper/broker.pid`
   - `~/.mcpbridge_wrapper/broker.sock`
5. Keep the same wrapper binary and package version across all clients that share the broker.

## Rollback to direct mode

1. Remove `--broker` from MCP config args.
2. Restart the MCP client.
3. Stop any running broker process:

```bash
mcpbridge-wrapper --broker-stop
```

4. Verify direct mode behavior by running one tool call and confirming no broker files are recreated.

## Limitations

- Broker mode currently uses local Unix socket paths and is intended for single-user local workflows.
- `--broker` automatically detects and removes stale socket/PID files left by a crashed daemon before spawning a new one.

## Security boundary

The broker socket is protected by two complementary mechanisms so that only the
same OS user can communicate with it:

1. **File permissions** — The socket file (`broker.sock`) is created with
   `0600` permissions (owner read/write only) as soon as the daemon starts.
   Other OS users cannot even open a connection to the socket.

2. **Peer credential verification** — Every accepted connection is verified
   using the operating system's peer credential API (`SO_PEERCRED` on Linux,
   `getpeereid()` on macOS/BSD). If the connecting process's effective UID
   differs from the broker's own UID, the connection is rejected immediately
   with a JSON-RPC `-32003` error and closed without disturbing active
   sessions.

This is intentionally a local-user security model: the broker is designed for
single-user workstations where all MCP clients run as the same macOS/Linux user
account.

### Troubleshooting

**"Forbidden: UID mismatch" (code -32003)** — The connecting process is running
as a different OS user than the broker daemon. Ensure client and daemon are
started under the same user account.

**"Permission denied" connecting to broker socket** — The socket file does not
have `0600` permissions or is owned by a different user. Check with
`ls -la ~/.mcpbridge_wrapper/broker.sock`. If the permissions are wrong, stop
the daemon and restart it so the socket is recreated with correct permissions.

## Related docs

- [Cursor Setup](cursor-setup.md)
- [Claude Setup](claude-setup.md)
- [Codex Setup](codex-setup.md)
- [Troubleshooting](troubleshooting.md)
