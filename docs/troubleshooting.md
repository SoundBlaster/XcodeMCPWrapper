# Troubleshooting Guide

**Setting up for the first time?** See [Quickstart](quickstart.md) for the recommended initial flow before diving into this error reference.

## Common Errors

### "Found 0 tools, 0 prompts, and 0 resources"

**Symptom:** MCP client connects successfully but reports 0 available tools

**Example log:**
```
Successfully connected to stdio server
Found 0 tools, 0 prompts, and 0 resources
```

**Cause:** Xcode Tools MCP is not enabled in Xcode settings. The mcpbridge connects to Xcode but the tool service is not running.

**Solution:**
1. Open **Xcode** > **Settings** (⌘,)
2. Select **Intelligence** in the sidebar
3. Under **Model Context Protocol**, toggle **Xcode Tools** ON
4. Restart your MCP client (Cursor/Zed/Claude)
5. Try again

**Diagnostic:** If you run the wrapper manually and see this message after sending `tools/list`:
```
⚠️  DIAGNOSTIC: Xcode Tools MCP service is not responding.
   This usually means Xcode Tools MCP is not enabled in Xcode settings.
```

This confirms the issue is with Xcode settings, not the wrapper.

### "MCP client shows 0 tools (green dot) after first broker connection"

**Symptom:** MCP client shows a green "connected" indicator but lists 0 tools, with no error
message. The client appears healthy but no Xcode tools are available.

**Root cause:** When the broker daemon starts a new upstream `xcrun mcpbridge` process for the
first time, Xcode shows a per-process "Allow Connection?" dialog. If an MCP client sends
`tools/list` *before* Xcode grants approval, it receives an empty tools list — and **caches it
permanently**. The client then shows 0 tools indefinitely, even after Xcode approval, because
it never re-fetches the list on its own.

**Per-process identity note:** Each unique binary path (or sandboxed identity) triggers a
*separate* Xcode dialog. This means:

- Direct-mode wrapper (`mcpbridge-wrapper` without `--broker`) → one approval dialog
- Broker daemon (`mcpbridge-wrapper --broker-daemon`) → a *different* approval dialog

After you approve each identity once, the permission persists for that binary path across
restarts. No re-approval is needed on subsequent sessions.

**Broker log signature:** While the approval dialog is showing, the broker reconnects several
times because the upstream `xcrun mcpbridge` cycles on EOF before stabilizing:

```
Upstream EOF detected; scheduling reconnect
Upstream EOF detected; scheduling reconnect
```

Once Xcode grants approval the reconnect loop stops and the upstream becomes healthy.

**Correct first-time setup sequence:**

1. Start the broker (or use `--broker` auto-start in your MCP client config).
2. Watch for the Xcode **"Allow Connection?"** dialog — it typically appears within a few seconds.
3. Click **Allow** in the Xcode dialog.
4. Verify the broker upstream is stable (check the broker log — reconnect messages should stop).
5. **Reload the MCP connection in your client** (see client-specific steps below).

> ℹ️ After step 2, do not send any MCP requests until step 5. Sending `tools/list` before
> approval caches the empty response in the client.

**Recovery after seeing 0 tools — client-specific steps:**

*Zed:*
1. Open `~/.config/zed/settings.json`.
2. Set `"enabled": false` for the `xcode-tools` context server.
3. Save the file and wait a few seconds.
4. Set `"enabled": true` and save again.
5. Wait for the spinner to complete — Zed re-fetches `tools/list` on each reconnect.

*Cursor:*
1. Open **Cursor** > **Settings** > **MCP** (or `~/.cursor/mcp.json`).
2. Toggle the `xcode-tools` server off, save, then toggle it back on.
3. Alternatively, restart Cursor entirely — it re-fetches `tools/list` on startup.

*Claude Code:*
```bash
# Remove and re-add the server to force a fresh tools/list fetch
claude mcp remove xcode
claude mcp add --transport stdio xcode -- \
  uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --broker
```
Or simply start a new Claude Code session — a fresh session always fetches tools on connect.

**Diagnostic:** Check the broker log for the reconnect pattern and confirm approval resolved it:

```bash
tail -50 "$HOME/.mcpbridge_wrapper/broker.log" | grep -E "EOF|reconnect|ready|tools"
```

After a successful approval and client reload you should see no new EOF entries and the
upstream should remain stable.

**Zed-specific escalation — green `0 tools` becomes red `Context server request timeout`:**

If Zed first shows a green connection with 0 tools and later turns red with
`Context server request timeout`, the broker daemon usually never reached a stable upstream
session within Zed's 60-second startup window. In that state, auto-spawn can leave Zed waiting
on a broker session that is still recovering from the first approval race.

The most reliable recovery is to switch that reconnect through a dedicated broker host:

1. Disable the `xcode-tools` context server in Zed (or quit Zed completely).
2. Stop the current broker daemon:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-stop
```

3. Start a dedicated broker host manually:

```bash
nohup uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-daemon \
  > "$HOME/.mcpbridge_wrapper/broker.log" 2>&1 &
```

4. Wait a few seconds, then verify the daemon is healthy:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-status
```

5. Re-enable the `xcode-tools` context server in Zed (or relaunch Zed).

If Xcode already approved `mcpbridge-broker`, the prompt should not reappear for the same binary
path. Zed now connects to an already-running broker instead of waiting for auto-spawn during its
startup timeout window.

**Xcode Agent Activity note:** Seeing several `mcpbridge-broker` rows with only one `Active`
status usually means Xcode is showing previous broker sessions or reconnect attempts. It does
**not** by itself mean multiple live broker daemons are running. Use `--broker-status` (or the
PID file under `~/.mcpbridge_wrapper/`) to confirm which daemon is actually alive.

### How do I confirm two editors share one broker daemon?

Use the dedicated-host verification flow instead of relying on Xcode's Agent
Activity rows.

```bash
# 1) One daemon identity
uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker-status

# 2) One shared broker state directory
ls -l "$HOME/.mcpbridge_wrapper/broker.pid" \
      "$HOME/.mcpbridge_wrapper/broker.sock" \
      "$HOME/.mcpbridge_wrapper/broker.version"

# 3) Optional structured view of the same host
# Add --web-ui-config if the host uses non-default host/port/auth settings.
mcpbridge-wrapper --tui
```

Then check:

1. `--broker-status` reports one daemon PID and one version.
2. The dashboard or TUI shows the same daemon PID/state you saw in
   `--broker-status`.
3. After both editors send one MCP request, the shared frontend shows live
   client activity without spawning a second host owner.
4. `~/.mcpbridge_wrapper/broker.log` does not keep printing repeated
   `Upstream EOF` / reconnect messages while the system is idle.

If you want the clearest operational model, switch both editors to one explicit
dedicated host (`--broker-daemon --web-ui`) and keep the editors themselves on
`--broker`.

---

### "Tool has output schema but did not return structured content"

**Symptom:** Error -32600 when using tools with Cursor

**Cause:** You're connecting directly to `xcrun mcpbridge` without the wrapper.

**Solution:**
1. Ensure your MCP client is configured to use the wrapper via **uvx** or `xcodemcpwrapper`
2. Not `xcrun mcpbridge` directly
3. See [Cursor Setup](cursor-setup.md) for configuration

### "Tool has output schema but did not return structured content" (empty result)

**Symptom:** Cursor or Codex reports a schema violation such as:

```
Tool has output schema but did not return structured content
```

even though the tool ran successfully and returned an empty result.

**Cause:** The Xcode MCP bridge returned `result.content: []` (empty content array)
without a `structuredContent` field. Strict MCP clients require `structuredContent`
on every `tools/call` response, even when the content list is empty.

**Solution:** mcpbridge-wrapper automatically injects `structuredContent: {}` for
empty-content tool responses. Ensure you are connecting through the wrapper:

```bash
# Correct — via wrapper
uvx mcpbridge-wrapper

# Incorrect — direct bridge connection (no transformation)
xcrun mcpbridge
```

If you are already using the wrapper and still see this error, verify you are on
version 0.5.0 or later:

```bash
uvx mcpbridge-wrapper --version
```

### "command not found: uvx"

**Symptom:** uvx command not found when using the recommended installation method

**Cause:** uv is not installed

**Solution:**

Install uv (which includes uvx):

```bash
# Using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Or using pip
pip install uv
```

After installation, restart your terminal or run:
```bash
source ~/.zshrc  # or ~/.bashrc
```

Then verify:
```bash
uvx --version
```

### "error: externally-managed-environment" (PEP 668)

**Symptom:** `make install`, `pip install`, or `pip3 install` fails with:

```text
error: externally-managed-environment
```

**Cause:** You're using a system/Homebrew-managed Python environment where global package installs are intentionally blocked.

**Solution (recommended):**

```bash
cd /path/to/XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
make install
```

**Important:** Creating a venv is not enough by itself. You must activate it before running `make install`.

Verify activation:

```bash
which python3
which pip
```

Both should point to `.venv/bin/...`.

If you already created a venv (for example `python3 -m venv .`), activate that exact path:

```bash
source bin/activate
```

Then rerun `make install`.

### "Xcode not found"

**Symptom:** Bridge fails to start, complaining about Xcode

**Cause:** Xcode is not running or not installed

**Solution:**
1. Ensure Xcode 26.3+ is installed
2. Open Xcode with a project
3. Enable Xcode Tools MCP Server in Settings > Intelligence
4. Try again

### "Permission denied" (Manual Installation Only)

**Symptom:** Cannot run xcodemcpwrapper

**Cause:** File is not executable

**Solution:**
```bash
chmod +x ~/bin/xcodemcpwrapper
```

### "command not found: xcodemcpwrapper" (Manual Installation Only)

**Symptom:** Shell cannot find the command

**Cause:** `~/bin` is not in PATH

**Solution:**
Add to `~/.zshrc` or `~/.bashrc`:
```bash
export PATH="$HOME/bin:$PATH"
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### "Web UI dependencies not installed" / `ModuleNotFoundError: uvicorn`

**Symptom:** Wrapper exits when client config includes `--web-ui` args.

**Cause:** The MCP config enables `--web-ui`, but the installed command is missing Web UI dependencies.

**Solution (uvx):**
Use `[webui]` extras in the uvx package source when Web UI args are enabled:
```bash
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --help
```

**Solution (manual install):**
```bash
cd /path/to/XcodeMCPWrapper
./scripts/install.sh --webui
```

Then restart your MCP client.

If you do not need Web UI, remove `--web-ui` and `--web-ui-port` from MCP config args.

### "Safari can't connect to the server" after MCP startup failure

**Symptom:** Browser cannot reach the dashboard URL (for example `http://localhost:8080`) after MCP startup fails with handshake/session errors.

**Cause:** In normal MCP mode, Web UI runs in the same wrapper process as bridge startup. If bridge initialization fails or the MCP client disconnects early, the process exits and dashboard availability is lost.

**Solution:**
Use standalone dashboard mode for diagnostics:

```bash
# uvx
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui-only --web-ui-port 8080

# manual install
xcodemcpwrapper --web-ui-only --web-ui-port 8080

# local development venv
/path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui-only --web-ui-port 8080
```

`--web-ui-only` starts only the dashboard service and skips bridge startup. Use this mode to keep Web UI reachable while you debug MCP client connection issues separately.

### `zsh: no matches found: mcpbridge-wrapper[webui]`

**Symptom:** Setup commands fail immediately in `zsh` before `uvx` runs.

**Cause:** `zsh` treats unquoted brackets as glob patterns.

**Solution:**
Quote (or escape) the extras package specifier:
```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Alternative escaped form:
```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper\\[webui\\] mcpbridge-wrapper --web-ui --web-ui-port 8080
```

### "Web UI port N is already in use"

**Symptom (bridge + Web UI mode):** Wrapper starts without a dashboard after printing:

```
Warning: Web UI port 8080 is already in use. Skipping Web UI startup — MCP bridge will run without the dashboard.
```

**Symptom (`--web-ui-only` mode):** Command exits with code 1 after printing:

```
Error: Web UI port 8080 is already in use. Stop the existing process and retry.
```

**Cause:** A stale wrapper process from a previous run (or a crashed client restart) is still occupying the port. Multiple processes can exist simultaneously — for example after a Cursor restart — because the old process is never explicitly stopped.

**One-command restart (recommended):**

```bash
# Local development (from repo root)
make webui-restart PORT=8080
```

```bash
# uvx usage
uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui-only --web-ui-restart --web-ui-port 8080
```

The restart flow attempts graceful shutdown first (`SIGTERM`) and only uses force-kill (`SIGKILL`) for listeners that do not exit in time.

**Manual fallback (if needed):**

```bash
# Kill the listener bound to the port
PORT=8080
PID=$(lsof -tiTCP:$PORT -sTCP:LISTEN | head -n1)
kill "$PID"

# If it survives (some builds do not exit on SIGTERM), force kill
sleep 0.5
ps -p "$PID" >/dev/null 2>&1 && kill -9 "$PID"

# Optionally clear other web-ui wrapper instances (case-insensitive pattern)
pkill -f -i "mcpbridge_wrapper --web-ui" || true

# Verify the port is now free (expected: no output)
lsof -nP -iTCP:$PORT -sTCP:LISTEN
```

After stopping the stale process, restart your MCP client (Cursor / Zed / Claude Code) or rerun one of the restart commands above.
Prefer `kill` (`SIGTERM`) first; use `kill -9` only when the process does not exit.

**Note:** Multiple wrapper processes can run simultaneously on *different* ports. Make sure you identify the PID bound specifically to the port you want, not just any `mcpbridge` process. If the port is immediately re-occupied, close/restart MCP clients (Cursor/Zed/Claude) that may auto-spawn a new wrapper process.

### "MCP tools are green, but dashboard is unreachable"

**Symptom:** Your MCP client reports connected tools, but `http://127.0.0.1:8080` (or your configured Web UI URL) does not open.

**Cause:** MCP bridge and Web UI hosting are related but not identical:

- MCP can stay healthy even if Web UI startup is skipped.
- Only one process can own a given Web UI `host:port`.
- Dashboard starts in a direct-mode owner (`--web-ui`) or a broker host (`--broker-daemon --web-ui`).
- `--broker --web-ui` only starts a dashboard when it must spawn a host; when attaching to an existing host it does not retrofit dashboard settings.
- If dashboard bind fails (port already in use), wrapper logs a warning and continues MCP without dashboard hosting.
- A healthy MCP status does not guarantee an active dashboard listener on the expected port.

**Diagnosis:**

```bash
# 1) Is anything listening on the expected dashboard port?
PORT=8080
lsof -nP -iTCP:$PORT -sTCP:LISTEN

# 2) Which wrapper processes are currently alive?
pgrep -af "xcodemcpwrapper|mcpbridge-wrapper|mcpbridge_wrapper"

# 3) If you expect broker-hosted dashboard, inspect broker host logs
LOG="$HOME/.mcpbridge_wrapper/broker.log"
test -f "$LOG" && rg -n "Web UI dashboard started|Skipping Web UI startup" "$LOG" | tail -n 10
```

If step 1 returns no listener, no process currently owns the dashboard port.

**Solution options:**

1. **Single dashboard owner (direct mode):** keep `--web-ui` on one client config only.
2. **Use separate dashboard ports:** assign unique `--web-ui-port` values per process.
3. **Unified broker single-config:** use `--broker --web-ui --web-ui-config <shared-path>` in all clients so one spawned host owns the dashboard.
4. **Dedicated host pattern:** run one `--broker-daemon --web-ui` process, keep clients on `--broker`, and monitor the same host from the dashboard and/or `--tui`.
5. **Standalone diagnostics:** run `--web-ui-only` when you need dashboard-only debugging independent from MCP startup.

See also:
- [Web UI Setup Guide](webui-setup.md#multi-agent-web-ui-ownership-model)
- [Broker Mode Guide](broker-mode.md#dedicated-host-frontend-workflow)

---

### "Tool charts are fresh, but Audit Log / Session Timeline look stale"

**Symptom:** Chart widgets (request counts, tool distribution) show new activity, but `/api/audit` and Session Timeline still show older entries.

**Cause:** Multi-process client reconnects can split writes across wrapper processes. Audit/session views depend on shared JSONL audit files in `audit.log_dir`; if processes are writing to different log directories or an outdated runtime is still serving UI, views can appear stale.

**Diagnosis:**

```bash
# 1) Verify active dashboard process and port
PORT=8080
lsof -i TCP:$PORT -sTCP:LISTEN

# 2) Check audit log directory configured in that process
curl -s http://127.0.0.1:$PORT/api/config | jq '.audit.log_dir'

# 3) Inspect recent shared audit entries on disk
LOG_DIR=$(curl -s http://127.0.0.1:$PORT/api/config | jq -r '.audit.log_dir')
ls -lt "$LOG_DIR"/audit_*.jsonl | head
tail -n 20 "$LOG_DIR"/audit_*.jsonl 2>/dev/null | tail -n 20
```

**Solution:**
- Ensure all wrapper processes use the same `audit.log_dir` (via shared `--web-ui-config`).
- Restart stale processes so the active dashboard serves current code/config.
- Re-test by issuing a tool call, then refresh `/api/audit` and `/api/sessions`.

**Note:** Session-duration ordering edge cases are tracked separately in `BUG-T20`.

---

### "Uptime still shows 1h 0m 0s" or behavior is unchanged after upgrade

**Symptom:** You upgraded to a newer release, but dashboard behavior still matches an older version (for example uptime stays `1h 0m 0s`).

**Cause:** A previously started wrapper process is still running from an older `uvx` cache environment. New installs do not replace already-running processes.

**Diagnosis:**

```bash
# 1) Find the process serving your Web UI port
PORT=8080
PID=$(lsof -tiTCP:$PORT -sTCP:LISTEN | head -n1)
ps -p "$PID" -o command=

# 2) Print the mcpbridge-wrapper version used by that exact process
PY=$(ps -p "$PID" -o command= | awk '{print $1}')
"$PY" -c 'import importlib.metadata as m; print(m.version("mcpbridge-wrapper"))'
```

If the reported version is older than expected, you are connected to a stale runtime.

**Recovery:**

```bash
# Stop the stale process
kill "$PID"

# Start with a refreshed uvx environment
uvx --refresh --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Then reload the dashboard and verify uptime increases:

```bash
curl -s http://127.0.0.1:8080/api/metrics | jq .uptime_seconds
sleep 2
curl -s http://127.0.0.1:8080/api/metrics | jq .uptime_seconds
```

The second value should be larger.

**Important:** Multiple wrapper processes can run at the same time (for different ports or restarts), which can mask upgrades. Always verify the version for the process bound to the port you are viewing.

### "Could not connect to broker socket ... within 10.0s"

**Symptom:** Broker mode prints a JSON-RPC error to the client:

```json
{"jsonrpc":"2.0","id":null,"error":{"code":-32001,"message":"Broker unavailable: Could not connect to broker socket ... within 10.0s"}}
```

Or exits with the error text in logs.

**Cause:** The broker socket is missing or not ready.

**Note:** When using `--broker`, stale socket/PID files from a crashed daemon are detected and removed automatically.

**First step:** Run `--doctor` for a structured diagnostic report:

```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper --doctor
```

**Manual check:**

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then echo "broker running"; else echo "broker not running"; fi; ls -l "$SOCK" 2>/dev/null || echo "socket missing"
```

If broker is not running, use `--broker` (auto-detects and spawns) or start it manually, then reconnect with `--broker`.

### "Warning: broker is running without --web-ui on port N"

**Symptom:** After connecting in broker mode, a warning appears on stderr:

```text
Warning: broker is running without --web-ui on port 8080. Restart the broker to enable the dashboard.
  Hint: stop the running broker (rm ~/.mcpbridge_wrapper/broker.sock ~/.mcpbridge_wrapper/broker.pid) then reconnect with --broker --web-ui.
```

**Cause:** You passed `--broker --web-ui` but the broker daemon that is already running was started *without* `--web-ui`. The wrapper detects that port `8080` (or your configured port) is not accepting connections and prints this actionable warning. The MCP session continues normally.

**Solution:**

Stop the running broker and reconnect so the new daemon starts with the dashboard enabled:

```bash
# Stop the running broker
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"
SOCK="$HOME/.mcpbridge_wrapper/broker.sock"
[ -f "$PID_FILE" ] && kill "$(cat "$PID_FILE")" 2>/dev/null || true
rm -f "$PID_FILE" "$SOCK"
```

Then restart your MCP client (Cursor / Zed / Claude Code). On the next connection `--broker --web-ui` will spawn a fresh daemon that includes the dashboard.

---

### "Broker already running (PID ...)"

**Symptom:** Dedicated broker host startup fails with:

```text
RuntimeError: Broker already running (PID ...)
```

**Cause:** A live broker process already owns the lock.

**Solution:**
1. Reuse the existing broker with `--broker`, or
2. Stop the existing PID first:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")"; fi
```

### Stale broker lock/socket recovery

When using `--broker`, stale socket/PID files are detected automatically: the proxy checks whether the socket is actually accepting connections and, if not, removes the stale files and spawns a fresh daemon. No manual cleanup is required in normal use.

If startup is repeatedly blocked by orphaned files in your environment, clean them explicitly:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ] && ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then rm -f "$PID_FILE"; fi; if [ -S "$SOCK" ]; then rm -f "$SOCK"; fi
```

### Broker fails to start: "Address already in use" or socket bind error

**Symptom:** Starting the broker daemon fails with an error like:

```
OSError: [Errno 98] Address already in use
```

**Cause:** The socket path is already bound by another process, or a stale socket
file was not cleaned up from a previous crash.

**Behaviour since v0.3.x:** When the broker transport fails to bind during startup,
the daemon automatically performs a full rollback — terminating the upstream
subprocess and removing PID/socket files — before re-raising the error. No orphaned
processes or stale files are left behind.

**Resolution:**

1. Check for an existing broker: `cat ~/.mcpbridge_wrapper/broker.pid` and
   verify whether that PID is still alive.
2. If no live broker exists, remove leftover files and retry:

```bash
rm -f ~/.mcpbridge_wrapper/broker.pid ~/.mcpbridge_wrapper/broker.sock
```

3. If the error persists, check that another application is not using the same
   socket path.

### Rollback to direct mode (verified flow)

1. Remove `--broker` from your MCP config command args.
2. Restart the MCP client.
3. Stop and clean broker state:

```bash
PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"; SOCK="$HOME/.mcpbridge_wrapper/broker.sock"; if [ -f "$PID_FILE" ]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; fi; rm -f "$PID_FILE" "$SOCK"
```

4. Run one MCP request and confirm direct mode is active (no broker file recreation).

### "Package Version" shows old release after version bump (development environment)

**Symptom:** You bumped `pyproject.toml` to a new version (for example `0.4.2`) and released to
PyPI, but `--doctor` still reports the old version for the local binary:

```
Python Runtime
- Package Version: 0.4.1        ← old version from .venv dist-info
...
Local Broker State
- Recorded Daemon Version: 0.4.2  ← broker started via uvx, fetched latest from PyPI
- Version Mismatch: yes (package 0.4.1)
```

**Cause:** The `mcpbridge-wrapper` command resolves to the editable install inside your repository
`.venv`. Package version metadata is stored in
`.venv/lib/pythonX.Y/site-packages/mcpbridge_wrapper-{VERSION}.dist-info/` and is written only
when `pip install -e .` runs. Bumping `pyproject.toml` alone does not update the dist-info — so
the installed binary still reports the version from the last `pip install -e .` invocation.

Meanwhile `uvx --from mcpbridge-wrapper` always fetches the latest published release from PyPI
independently of your local `.venv`, so the broker daemon it starts writes the new version to
`broker.version`. The mismatch is an artifact of the dev environment, not a real compatibility
problem.

**Affected:** Repository contributors and maintainers with `.venv/bin` on their `PATH` or with
the venv activated. End users running `uvx` are never affected.

**Fix:**

```bash
# From the repository root, reinstall the editable package to refresh dist-info
.venv/bin/pip install -e .

# Verify the version now matches
mcpbridge-wrapper --doctor | grep "Package Version"
```

Or, if you have the venv activated:

```bash
pip install -e .
```

After reinstalling, `--doctor` should show matching versions and no mismatch.

---

## Debug Mode

For verbose output, check the stderr stream:

### uvx method:
```bash
uvx --from mcpbridge-wrapper mcpbridge-wrapper 2>&1 | tee wrapper.log
```

### Manual installation:
```bash
xcodemcpwrapper 2>&1 | tee wrapper.log
```

## Getting Help

If issues persist:
1. Check [GitHub Issues](https://github.com/SoundBlaster/XcodeMCPWrapper/issues)
2. Run tests: `pytest tests/`
3. Verify installation:
   - uvx method (base): `uvx --from mcpbridge-wrapper mcpbridge-wrapper --help`
   - uvx method (Web UI): `uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --help`
   - pip method: `pip show mcpbridge-wrapper`
   - manual method: `which xcodemcpwrapper`
