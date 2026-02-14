# Troubleshooting

Common issues and their solutions.

## Error: "Found 0 tools, 0 prompts, and 0 resources"

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

## Error: "Tool XcodeListWindows has an output schema but did not return structured content"

**Symptom:** MCP client shows this error when trying to use Xcode tools.

**Cause:** You're not using the wrapper. Xcode's mcpbridge returns responses without the required `structuredContent` field.

**Solution:**
1. Ensure your MCP client is configured to use the wrapper via **uvx** or `xcodemcpwrapper`
2. Not `xcrun mcpbridge` directly
3. See <doc:CursorSetup> for configuration

## Error: "command not found: uvx"

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

## Error: "externally-managed-environment" (PEP 668)

**Symptom:** `make install`, `pip install`, or `pip3 install` fails with:

```text
error: externally-managed-environment
```

**Cause:** You're using a system/Homebrew-managed Python environment where global installs are blocked.

**Solution (recommended):**

```bash
cd /path/to/XcodeMCPWrapper
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
make install
```

**Important:** Creating a virtual environment is not enough by itself. You must activate it before running `make install`.

Verify activation:

```bash
which python3
which pip
```

Both should point to `.venv/bin/...`.

If you created the virtual environment with `python3 -m venv .`, activate it with:

```bash
source bin/activate
```

## Xcode Not Found

**Symptom:** Tools report "Xcode is not running" or similar.

**Cause:** Xcode must be running with a project open for tools to function.

**Solution:**
1. Open Xcode
2. Open your project (`.xcodeproj` or `.xcworkspace`)
3. Enable Xcode Tools MCP Server in Xcode Settings > Intelligence
4. Try again

## Wrapper Not Executable (Manual Installation Only)

**Symptom:** Permission denied when running wrapper.

**Solution:**
```bash
chmod +x ~/bin/xcodemcpwrapper
```

## Error: "Web UI dependencies not installed" / `ModuleNotFoundError: uvicorn`

**Symptom:** Wrapper exits when MCP client config includes `--web-ui` args.

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

## Error: `zsh: no matches found: mcpbridge-wrapper[webui]`

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

## Error: "Uptime still shows 1h 0m 0s" or behavior is unchanged after upgrade

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

## Tool Returns Empty Results

**Symptom:** Tools execute but return no data.

**Cause:** The `tabIdentifier` may be invalid or the project may not be properly loaded.

**Solution:**
1. Call `XcodeListWindows` to get the current valid `tabIdentifier`
2. Ensure the project is fully loaded in Xcode (not still indexing)

## Performance Issues

**Symptom:** Slow response times.

**Solutions:**
1. Check Xcode is not busy indexing or building
2. Verify the wrapper process is running
3. Restart the MCP client connection

## Debug Mode

To see what's happening under the hood:

### uvx method:
```bash
# Test wrapper via uvx
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

### Manual installation:
```bash
# Test wrapper directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | ~/bin/xcodemcpwrapper
```

## Still Having Issues?

1. Check the GitHub Issues page
2. Verify your Xcode version (26.3+ required)
3. Check Python version (3.7+ required)
4. Review the wrapper logs (if available in your MCP client)
