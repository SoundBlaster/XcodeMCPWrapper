# Broker Mode Guide

Broker mode lets short-lived MCP client processes share a single long-lived upstream
`xcrun mcpbridge` session.

**New here?** Start with the [Quickstart](quickstart.md) for a step-by-step walkthrough.

---

## Quick setup (recommended path)

Two commands are all you need for the common case:

**1. Start the broker daemon** (once, in a terminal):

```bash
nohup uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-daemon --web-ui \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

> **First-time only:** Xcode shows an "Allow Connection?" dialog. Click **Allow** and
> wait for the reconnect loop to stop before connecting clients.

**2. Configure every MCP client with `--broker`** (they all attach to the running daemon):

```bash
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

That's the entire recommended path. The daemon runs once; clients attach and detach
as needed. See [Client configuration examples](#client-configuration-examples) for
per-client config snippets.

---

## Verify it is working

```bash
# Confirm broker is running and version matches
mcpbridge-wrapper --broker-status

# Watch live broker events (Ctrl-C to exit)
tail -f "$HOME/.mcpbridge_wrapper/broker.log"

# Open the browser dashboard
open http://127.0.0.1:8080

# Or use the terminal UI (no browser required)
mcpbridge-wrapper --tui
```

`--broker-status` prints daemon PID, version, and socket path. The dashboard and
`--tui` show live client sessions, tool call activity, and upstream status.

---

## Failure recovery

Use these three tools in order when anything looks wrong:

### 1. Check broker health

```bash
mcpbridge-wrapper --broker-status
```

Reports whether the daemon is alive, its PID, and whether its version matches the
installed wrapper. Version mismatch is the most common cause of unexpected behavior
after an upgrade.

### 2. Run the diagnostic report

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --doctor
```

`--doctor` connects to the running broker, probes the upstream bridge and dashboard,
and prints a structured pass/warn/fail report with suggested fixes. Run this as the
first step when any part of the stack looks unhealthy.

### 3. Inspect live state

```bash
mcpbridge-wrapper --tui
```

Opens a live terminal view of the running daemon: upstream connection state,
reconnect history, client sessions, and recent errors.

### Common recovery steps

| Symptom | Recovery |
|---------|----------|
| `--broker-status` shows "not running" | Restart the daemon (see [Quick setup](#quick-setup-recommended-path)) |
| Client shows 0 tools after Xcode approval | Reload/toggle the client; see [Troubleshooting](troubleshooting.md#mcp-client-shows-0-tools-green-dot-after-first-broker-connection) |
| Dashboard unreachable | `--doctor` → review Web UI findings |
| Version mismatch after upgrade | `mcpbridge-wrapper --broker-stop`, then restart daemon |
| Stale socket / PID file | `mcpbridge-wrapper --broker-stop` (or `--broker` auto-cleans on connect) |

### Restart the broker

```bash
mcpbridge-wrapper --broker-stop
# then restart with nohup ... --broker-daemon
```

---

## Mode summary

| Flag | Role |
|------|------|
| *(none — default)* | `direct`: each wrapper process launches its own upstream bridge. |
| `--broker-daemon` | **Daemon host**: long-lived process that owns the upstream bridge and accepts client connections on a Unix socket. Start this once, then point clients at it. |
| `--broker` | **Proxy + auto-detect** *(recommended)*: connects to a running broker if one is alive, spawns a new daemon otherwise. Automatically recovers stale socket/PID files left by a crashed daemon. |

Use broker mode when you want lower process churn across repeated MCP client restarts.

## Singleton broker host behavior

Broker mode keeps one long-lived daemon per local macOS user. The daemon owns the
single upstream `xcrun mcpbridge` session and every `--broker` client connects to
that daemon through `~/.mcpbridge_wrapper/broker.sock`. This includes `uvx`
clients such as:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper", "mcpbridge-wrapper", "--broker"]
    }
  }
}
```

If a short-lived proxy has a different package version than the live daemon, the
proxy reuses that daemon and prints a warning instead of stopping and replacing it
automatically. Restart the daemon explicitly when you choose to upgrade the host:

```bash
mcpbridge-wrapper --broker-stop
mcpbridge-wrapper --broker-daemon --web-ui
```

With `uvx`, the first client that needs to auto-spawn the daemon also determines
the daemon host identity that Xcode sees. That identity is usually a Python
executable from the `uvx` runtime/cache. For the most stable Xcode permission
identity, start a dedicated broker host from a fixed path, or pin auto-spawn to a
stable launcher with `MCPBRIDGE_WRAPPER_BROKER_HOST_CMD`. The configured command
is used only when `--broker` needs to auto-spawn a daemon; existing daemons are
reused.

```bash
export MCPBRIDGE_WRAPPER_BROKER_HOST_CMD="/Users/egor/bin/mcpbridge-wrapper-host"
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker --web-ui
```

The daemon writes host identity metadata to:

```text
~/.mcpbridge_wrapper/broker.host.json
```

Use `mcpbridge-wrapper --broker-status` or `mcpbridge-wrapper --doctor` to inspect
the recorded host executable.

---

## Multi-agent topology and Web UI ownership

Recommended topology for multiple agents/clients:

1. **Dedicated host frontend workflow (recommended when visibility matters):**
   run one explicit broker host with `--broker-daemon --web-ui`, configure
   clients with `--broker`, and attach the browser dashboard and/or `--tui` to
   that same host.
2. **Unified single-config auto-spawn:** use the same client args everywhere:
   `--broker --web-ui --web-ui-config <shared-path>` when you want the first
   client to own broker + dashboard startup implicitly.

Web UI behavior in broker modes:

- `--broker-daemon --web-ui` starts broker + dashboard in one host process.
- `--broker --web-ui` forwards Web UI flags to the spawned daemon when auto-start is needed; if a broker is already running without `--web-ui`, a warning is printed to stderr.
- When `--broker` reuses an already-running daemon, it does not change that daemon's dashboard state.
- `--tui` is an operator frontend for an already-running dashboard; it does not start broker or Web UI ownership by itself.
- Only one process can own a given Web UI `host:port`.
- If dashboard bind fails (for example port already in use), broker transport continues and only dashboard startup is skipped.

---

## Paths used by broker mode

By default, broker state is stored in `~/.mcpbridge_wrapper/`:

- Socket: `~/.mcpbridge_wrapper/broker.sock`
- PID file: `~/.mcpbridge_wrapper/broker.pid`
- Recommended log: `~/.mcpbridge_wrapper/broker.log`

---

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

### Dedicated host frontend workflow

Prefer this pattern when you run more than one editor/client and want one clear
daemon owner, one approval path, and one explicit place to inspect broker
health.

Use it when:

- you want to start and stop the broker independently from editor restarts
- you want one known PID/log/socket identity to verify across multiple editors
- you want browser/TUI monitoring even when no editor is currently spawning the
  broker
- you are debugging reconnects, approval churn, or dashboard ownership

1. Start one dedicated broker host:

```bash
nohup uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-daemon --web-ui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json" \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

2. Attach one or both frontend surfaces to that same host:

```bash
# Browser dashboard (adjust host:port if your webui.json differs from defaults)
open http://127.0.0.1:8080

# Terminal UI (uses the same host/port/auth from the Web UI config)
mcpbridge-wrapper --tui --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

3. Configure every editor/client with `--broker` only. The clients attach to the
   running host instead of competing to own startup.

4. Verify that multiple editors share one daemon:

```bash
# One daemon identity
mcpbridge-wrapper --broker-status

# One shared broker state directory
ls -l "$HOME/.mcpbridge_wrapper/broker.pid" \
      "$HOME/.mcpbridge_wrapper/broker.sock" \
      "$HOME/.mcpbridge_wrapper/broker.version"

# Recent broker events should settle after approval
tail -n 20 "$HOME/.mcpbridge_wrapper/broker.log"
```

Then confirm the same daemon PID/state appears in the dashboard or TUI. With
both editors connected, the frontend should show one shared daemon and live
client sessions instead of separate host owners.

Important: Xcode may still show several `mcpbridge-broker` rows in Agent
Activity. Treat those rows as session/reconnect history, not as proof of
multiple live daemon hosts. Use `--broker-status`, broker files, and the shared
frontend state as the source of truth.

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

For day-to-day operator visibility, prefer the dashboard or `--tui`; the raw
log is most useful for reconnect details and startup diagnostics.

### Stop

```bash
mcpbridge-wrapper --broker-stop
```

Sends SIGTERM to the running daemon and waits up to 3 seconds for a clean exit. If the daemon exits, PID/socket/version files are removed. If it does not exit in time, the command returns an error and preserves state files for manual recovery.

---

## Version management

When upgrading `mcpbridge-wrapper` (via `pip install`, `uvx`, or `./scripts/install.sh`):

1. The **install script** automatically stops any running broker daemon.
2. On next `--broker` launch, the proxy compares its version against the daemon's
   version file (`~/.mcpbridge_wrapper/broker.version`). If versions differ, the
   stale daemon is stopped and a fresh one is spawned automatically.
3. Use `--broker-status` to verify the running daemon matches the installed version.

If an older daemon was started before the upgrade and you want to force an immediate
restart, run `mcpbridge-wrapper --broker-stop` followed by any `--broker` command.

---

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

If you prefer explicit host lifecycle management, use the
[dedicated host frontend workflow](#dedicated-host-frontend-workflow): start
one `--broker-daemon --web-ui` process manually and configure clients with
`--broker`.

---

## Migration from direct mode to broker mode

1. Back up your current MCP client configuration.
2. Choose one rollout pattern:
   - Dedicated host frontend workflow: start `--broker-daemon --web-ui` once,
     attach dashboard/TUI explicitly, and set clients to `--broker`.
   - Unified config: set clients to `--broker --web-ui --web-ui-config <shared-path>`.
3. Restart each MCP client.
4. Run a first MCP request and verify broker files exist:
   - `~/.mcpbridge_wrapper/broker.pid`
   - `~/.mcpbridge_wrapper/broker.sock`
5. If you are using the dedicated-host workflow, also verify that the dashboard
   or TUI reports the same daemon PID you saw in `--broker-status`.
6. Keep the same wrapper binary and package version across all clients that share the broker.

---

## Rollback to direct mode

1. Remove `--broker` from MCP config args.
2. Restart the MCP client.
3. Stop any running broker process:

```bash
mcpbridge-wrapper --broker-stop
```

4. Verify direct mode behavior by running one tool call and confirming no broker files are recreated.

---

## Limitations

- Broker mode currently uses local Unix socket paths and is intended for single-user local workflows.
- `--broker` automatically detects and removes stale socket/PID files left by a crashed daemon before spawning a new one.

---

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

---

## Related docs

- [Quickstart](quickstart.md)
- [Cursor Setup](cursor-setup.md)
- [Claude Setup](claude-setup.md)
- [Codex Setup](codex-setup.md)
- [Troubleshooting](troubleshooting.md)
