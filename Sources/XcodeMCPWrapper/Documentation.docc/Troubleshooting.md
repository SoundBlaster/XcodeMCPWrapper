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
uvx --from mcpbridge-wrapper[webui] mcpbridge-wrapper --help
```

**Solution (manual install):**
```bash
cd /path/to/XcodeMCPWrapper
./scripts/install.sh --webui
```

Then restart your MCP client.

If you do not need Web UI, remove `--web-ui` and `--web-ui-port` from MCP config args.

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
