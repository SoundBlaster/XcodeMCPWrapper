# Broker Mode Guide

Broker mode lets short-lived MCP client processes share a single long-lived upstream
`xcrun mcpbridge` session.

## Mode summary

| Flag | Role |
|------|------|
| *(none — default)* | `direct`: each wrapper process launches its own upstream bridge. |
| `--broker-daemon` | **Daemon host**: long-lived process that owns the upstream bridge and accepts client connections on a Unix socket. Start this once, then point clients at it. |
| `--broker-connect` | **Proxy**: connects to an already-running broker socket and forwards stdio. |
| `--broker-spawn` | **Proxy + auto-start**: same as `--broker-connect`, but also spawns a broker daemon if none is available. |

Use broker mode when you want lower process churn across repeated MCP client restarts.

## Multi-agent topology and Web UI ownership

Recommended topology for multiple agents/clients:

1. **Unified single-config (recommended):** use the same client args everywhere:
   `--broker-spawn --web-ui --web-ui-config <shared-path>`.
2. **Dedicated host alternative:** run one explicit broker host with
   `--broker-daemon --web-ui` and configure clients with `--broker-connect`.

Web UI behavior in broker modes:

- `--broker-daemon --web-ui` starts broker + dashboard in one host process.
- `--broker-spawn --web-ui` forwards Web UI flags to the spawned daemon when auto-start is needed.
- `--broker-connect` never starts a dashboard by itself.
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
nohup mcpbridge-wrapper --broker-daemon --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json" \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
echo "Broker started (PID $!)"
```

Or using `uvx`:

```bash
nohup uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-daemon --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json" \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

Then configure MCP clients with `--broker-connect` (see client examples below).

`--broker-spawn` is available as a best-effort alternative that auto-starts the daemon when needed (including dashboard args):

```bash
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-spawn --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
```

### Status

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"
SOCK="$HOME/.mcpbridge_wrapper/broker.sock"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "broker: running (pid $(cat "$PID_FILE"))"
else
  echo "broker: stopped"
fi

if [ -S "$SOCK" ]; then
  echo "socket: present ($SOCK)"
else
  echo "socket: missing ($SOCK)"
fi
```

### Logs

```bash
tail -f "$HOME/.mcpbridge_wrapper/broker.log"
```

### Stop

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"
SOCK="$HOME/.mcpbridge_wrapper/broker.sock"

if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
fi
rm -f "$PID_FILE" "$SOCK"
```

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
        "--broker-spawn",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.mcpbridge_wrapper/webui.json"
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
        "--broker-spawn",
        "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.mcpbridge_wrapper/webui.json"
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
  --broker-spawn --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
```

### Codex CLI

```bash
codex mcp add xcode -- \
  uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-spawn --web-ui --web-ui-config "$HOME/.mcpbridge_wrapper/webui.json"
```

### Dedicated host + connect-only alternative

If you prefer explicit host lifecycle management, start one `--broker-daemon --web-ui` process manually and configure clients with `--broker-connect` only.

## Migration from direct mode to broker mode

1. Back up your current MCP client configuration.
2. Choose one rollout pattern:
   - Unified config: set clients to `--broker-spawn --web-ui --web-ui-config <shared-path>`.
   - Dedicated host: start `--broker-daemon --web-ui` once and set clients to `--broker-connect`.
3. Restart each MCP client.
4. Run a first MCP request and verify broker files exist:
   - `~/.mcpbridge_wrapper/broker.pid`
   - `~/.mcpbridge_wrapper/broker.sock`
5. Keep the same wrapper binary and package version across all clients that share the broker.

## Rollback to direct mode

1. Remove `--broker-connect` / `--broker-spawn` from MCP config args.
2. Restart the MCP client.
3. Stop any running broker process and remove stale files:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"
SOCK="$HOME/.mcpbridge_wrapper/broker.sock"
if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi
rm -f "$PID_FILE" "$SOCK"
```

4. Verify direct mode behavior by running one tool call and confirming no broker files are recreated.

## Limitations

- Broker mode currently uses local Unix socket paths and is intended for single-user local workflows.
- If a stale PID or socket file remains after a crash, clean it up before reconnecting.
- Auto-spawn may fail if a ready socket is not created in time; use `--broker-connect` with an explicitly started broker host in that case.

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
