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
   - uvx method: `uvx --from mcpbridge-wrapper mcpbridge-wrapper --help`
   - pip method: `pip show mcpbridge-wrapper`
   - manual method: `which xcodemcpwrapper`
