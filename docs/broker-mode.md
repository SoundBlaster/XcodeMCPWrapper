# Broker Mode Guide

Broker mode lets short-lived MCP client processes share a single long-lived upstream
`xcrun mcpbridge` session.

## Mode summary

- `direct` (default): each wrapper process launches its own upstream bridge.
- `broker-connect`: wrapper process connects to an already-running broker socket.
- `broker-spawn`: same as `broker-connect`, but also attempts to auto-start a broker if none is available.

Use broker mode when you want lower process churn across repeated MCP client restarts.

## Paths used by broker mode

By default, broker state is stored in `~/.mcpbridge_wrapper/`:

- Socket: `~/.mcpbridge_wrapper/broker.sock`
- PID file: `~/.mcpbridge_wrapper/broker.pid`

## One-command operational flows

### Start

For predictable operation, start a dedicated background broker host first:

```bash
PYTHONPATH=src nohup python3 -c 'import asyncio; from mcpbridge_wrapper.broker.daemon import BrokerDaemon; from mcpbridge_wrapper.broker.transport import UnixSocketServer; from mcpbridge_wrapper.broker.types import BrokerConfig; cfg=BrokerConfig.default(); d=BrokerDaemon(cfg); t=UnixSocketServer(cfg,d); d._transport=t; asyncio.run(d.run_forever())' > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

Then configure MCP clients with `--broker-connect`.

`--broker-spawn` is available as a best-effort auto-start mode:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-spawn
```

### Status

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then echo "broker: running (pid $(cat "$PID_FILE"))"; else echo "broker: stopped"; fi; if [ -S "$SOCK" ]; then echo "socket: present ($SOCK)"; else echo "socket: missing ($SOCK)"; fi
```

### Logs

```bash
tail -f "$HOME/.mcpbridge_wrapper/broker.log"
```

### Stop

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi; rm -f "$PID_FILE" "$SOCK"
```

## Client configuration examples

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "mcpbridge-wrapper",
        "mcpbridge-wrapper",
        "--broker-connect"
      ]
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect
```

### Codex CLI

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-connect
```

## Migration from direct mode to broker mode

1. Back up your current MCP client configuration.
2. Start a broker host (recommended) and set MCP clients to `--broker-connect`.
3. Optional alternative: use `--broker-spawn` for best-effort auto-start.
4. Restart your MCP client.
5. Run a first MCP request and verify broker files exist:
   - `~/.mcpbridge_wrapper/broker.pid`
   - `~/.mcpbridge_wrapper/broker.sock`
6. Keep the same wrapper binary and package version across all clients that share the broker.

## Rollback to direct mode

1. Remove `--broker-connect` / `--broker-spawn` from MCP config args.
2. Restart the MCP client.
3. Stop any running broker process and remove stale files:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi; rm -f "$PID_FILE" "$SOCK"
```

4. Verify direct mode behavior by running one tool call and confirming no broker files are recreated.

## Limitations

- Broker mode currently uses local Unix socket paths and is intended for single-user local workflows.
- If a stale PID or socket file remains after a crash, clean it up before reconnecting.
- Auto-spawn may fail if a ready socket is not created in time; use `--broker-connect` with an explicitly started broker host in that case.

## Related docs

- [Cursor Setup](cursor-setup.md)
- [Claude Setup](claude-setup.md)
- [Codex Setup](codex-setup.md)
- [Troubleshooting](troubleshooting.md)
