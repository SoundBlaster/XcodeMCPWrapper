# Environment Variables

## Optional Variables

### `MCP_XCODE_PID`

Manually specify the Xcode process ID when auto-detection fails.

```bash
export MCP_XCODE_PID=$(pgrep -x Xcode)
mcpbridge-wrapper
```

Rarely needed for external clients as mcpbridge auto-detects the correct Xcode instance.

### `MCP_XCODE_SESSION_ID`

UUID identifying an Xcode tool session.

```bash
export MCP_XCODE_SESSION_ID="your-session-uuid"
```

Rarely needed for external MCP clients.

## Usage Example

```bash
# Get Xcode PID
XCODE_PID=$(pgrep -x Xcode)

# Run with explicit PID
MCP_XCODE_PID=$XCODE_PID mcpbridge-wrapper
```
