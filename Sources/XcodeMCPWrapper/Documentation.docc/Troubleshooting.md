# Troubleshooting

Common issues and their solutions.

## Error: "Tool XcodeListWindows has an output schema but did not return structured content"

**Symptom:** MCP client shows this error when trying to use Xcode tools.

**Cause:** You're not using the wrapper. Xcode's mcpbridge returns responses without the required `structuredContent` field.

**Solution:**
1. Ensure the wrapper is installed: `ls -l ~/bin/xcodemcpwrapper`
2. Check your MCP client configuration points to the wrapper
3. Restart your MCP client after configuration changes

## Xcode Not Found

**Symptom:** Tools report "Xcode is not running" or similar.

**Cause:** Xcode must be running with a project open for tools to function.

**Solution:**
1. Open Xcode
2. Open your project (`.xcodeproj` or `.xcworkspace`)
3. Enable Xcode Tools MCP Server in Xcode Settings > Intelligence
4. Try again

## Wrapper Not Executable

**Symptom:** Permission denied when running wrapper.

**Solution:**
```bash
chmod +x ~/bin/xcodemcpwrapper
```

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

```bash
# Test wrapper directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | ~/bin/xcodemcpwrapper
```

## Still Having Issues?

1. Check the GitHub Issues page
2. Verify your Xcode version (26.3+ required)
3. Check Python version (3.7+ required)
4. Review the wrapper logs (if available in your MCP client)
