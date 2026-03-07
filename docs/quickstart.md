# Quickstart: Broker Setup in 5 Steps

This guide gets you from zero to a working broker-mode setup with the first MCP
client verified. If you hit any problem along the way, jump to
[Failure recovery](#failure-recovery) at the bottom of this page or open
[Troubleshooting](troubleshooting.md).

---

## Prerequisites

- macOS with **Xcode 26.3** or later installed and open
- **uv / uvx** installed — run `uvx --version` to verify, or install:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## Step 1 — Enable Xcode Tools MCP in Xcode

Open **Xcode → Settings** (`⌘,`) → **Intelligence** → toggle **Xcode Tools** on.

> If this toggle is off, your MCP client will connect but report 0 tools.

---

## Step 2 — Start the broker daemon

Run this once in a terminal. The daemon stays alive in the background and handles
all MCP client connections.

```bash
nohup uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker-daemon --web-ui \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
echo "Broker started (PID $!)"
```

> **First-time run:** Xcode may show an **"Allow Connection?"** dialog within a few
> seconds. Click **Allow**. Wait until the reconnect messages in the log stop before
> continuing.
>
> ```bash
> tail -f "$HOME/.mcpbridge_wrapper/broker.log"
> # Look for the reconnect loop to stop — then Ctrl-C
> ```

---

## Step 3 — Verify the broker is healthy

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-status
```

Expected output includes a live PID and a matching version. Example:

```
Broker status: running
  PID:     12345
  Version: 0.4.1
  Socket:  /Users/you/.mcpbridge_wrapper/broker.sock
```

If you see **"broker not running"** or a version mismatch, see
[Failure recovery](#failure-recovery).

---

## Step 4 — Add one MCP client

Pick your client and add the broker config. Every client uses the same `--broker`
flag — they all attach to the daemon you started in Step 2.

**Claude Code:**
```bash
claude mcp add --transport stdio xcode -- \
  uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper \
  --broker --web-ui \
  --web-ui-config "$HOME/.config/xcodemcpwrapper/webui.json"
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from", "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--broker", "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.config/xcodemcpwrapper/webui.json"
      ]
    }
  }
}
```

**Zed** (`~/.config/zed/settings.json`):
```json
{
  "context_servers": {
    "xcode-tools": {
      "command": "uvx",
      "args": [
        "--from", "mcpbridge-wrapper[webui]",
        "mcpbridge-wrapper",
        "--broker", "--web-ui",
        "--web-ui-config",
        "/Users/YOUR_USERNAME/.config/xcodemcpwrapper/webui.json"
      ],
      "env": {}
    }
  }
}
```

---

## Step 5 — Verify the tools are available

Restart or reload the MCP client you configured, then run one Xcode tool call (for
example, ask Claude Code to list files in your Xcode project). You should see a
non-empty tool result.

Optionally open the dashboard:

```bash
open http://127.0.0.1:8080
```

The dashboard shows connected clients, tool call activity, and broker health.

---

## Failure recovery

If something goes wrong, use these three commands to diagnose and recover:

### 1. Check broker health

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-status
```

Reports whether the daemon is running, its PID, and whether the version matches
the installed wrapper.

### 2. Run the diagnostic report

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --doctor
```

`--doctor` connects to the running broker, probes the upstream bridge, and prints
a structured report with pass/warn/fail findings and suggested fixes. Run this
first when any part of the stack looks unhealthy.

### 3. Inspect live broker state (TUI)

```bash
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --tui
```

Opens a live terminal view of the broker daemon: reconnect history, client
sessions, upstream status, and recent errors. No browser required.

### Common recoveries

| Symptom | Recovery |
|---------|----------|
| `--broker-status` shows "not running" | Repeat Step 2 |
| Client shows 0 tools after approval | Reload or toggle the client off and on (see [Troubleshooting](troubleshooting.md#mcp-client-shows-0-tools-green-dot-after-first-broker-connection)) |
| Dashboard unreachable | `--doctor` → check Web UI findings; confirm port 8080 is free |
| Version mismatch warning | `mcpbridge-wrapper --broker-stop`, then repeat Step 2 |
| Stale socket / PID file | `mcpbridge-wrapper --broker-stop` cleans up automatically when used with `--broker` |

### Restart the broker

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-stop
# then repeat Step 2
```

---

## Next steps

- Add more MCP clients — they all use the same `--broker` args, sharing one daemon
- See [Broker Mode Guide](broker-mode.md) for advanced topology options
- See [Troubleshooting](troubleshooting.md) for a full error reference
