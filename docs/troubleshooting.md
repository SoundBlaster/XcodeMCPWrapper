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

**Diagnostic:** If you run `mcpbridge-wrapper` manually and see this message after sending `tools/list`:
```
⚠️  DIAGNOSTIC: Xcode Tools MCP service is not responding.
   This usually means Xcode Tools MCP is not enabled in Xcode settings.
```

This confirms the issue is with Xcode settings, not the wrapper.

### "Tool has output schema but did not return structured content"

**Symptom:** Error -32600 when using tools with Cursor

**Cause:** You're connecting directly to `xcrun mcpbridge` without the wrapper.

**Solution:** 
1. Ensure your MCP client is configured to use `mcpbridge-wrapper`
2. Not `xcrun mcpbridge` directly
3. See [Cursor Setup](cursor-setup.md) for configuration

### "Xcode not found"

**Symptom:** Bridge fails to start, complaining about Xcode

**Cause:** Xcode is not running or not installed

**Solution:**
1. Ensure Xcode 26.3+ is installed
2. Open Xcode with a project
3. Enable Xcode Tools MCP Server in Settings > Intelligence
4. Try again

### "Permission denied"

**Symptom:** Cannot run mcpbridge-wrapper

**Cause:** File is not executable

**Solution:**
```bash
chmod +x ~/bin/mcpbridge-wrapper
```

### "command not found: mcpbridge-wrapper"

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

```bash
mcpbridge-wrapper 2>&1 | tee wrapper.log
```

## Getting Help

If issues persist:
1. Check [GitHub Issues](https://github.com/yourusername/mcpbridge-wrapper/issues)
2. Run tests: `pytest tests/`
3. Verify installation: `pip show mcpbridge-wrapper`
