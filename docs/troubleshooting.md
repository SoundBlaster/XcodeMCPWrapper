# Troubleshooting Guide

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

### "Tool has output schema but did not return structured content"

**Symptom:** Error -32600 when using tools with Cursor

**Cause:** You're connecting directly to `xcrun mcpbridge` without the wrapper.

**Solution:** 
1. Ensure your MCP client is configured to use the wrapper via **uvx** or `xcodemcpwrapper`
2. Not `xcrun mcpbridge` directly
3. See [Cursor Setup](cursor-setup.md) for configuration

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

**Diagnosis:**

```bash
# Find the PID of the process listening on the Web UI port (default 8080)
PORT=8080
lsof -i TCP:$PORT -sTCP:LISTEN

# Alternatively, search by process name
ps aux | grep mcpbridge
```

Both commands show the PID in the second column (`PID`).

**Recovery:**

```bash
# Kill the stale process by PID
kill <PID>

# Or kill all wrapper/bridge processes in one step
pkill -f mcpbridge
```

After stopping the stale process, restart your MCP client (Cursor / Zed / Claude Code) or re-run the `--web-ui-only` command and the port should now be free.

**Note:** Multiple wrapper processes can run simultaneously on *different* ports. Make sure you identify the PID bound specifically to the port you want, not just any `mcpbridge` process.

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
