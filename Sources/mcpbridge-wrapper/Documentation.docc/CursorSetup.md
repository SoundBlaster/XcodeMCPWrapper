# Cursor Setup

Configure Cursor to use Xcode MCP tools via mcpbridge-wrapper.

## Configuration Steps

### 1. Install mcpbridge-wrapper

```bash
./scripts/install.sh
```

### 2. Get Your Username

```bash
whoami
```

### 3. Edit Cursor MCP Configuration

Open or create `~/.cursor/mcp.json`:

```bash
mkdir -p ~/.cursor
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper"
    }
  }
}
EOF
```

Replace `YOUR_USERNAME` with the output from `whoami`.

### 4. Restart Cursor

Quit and reopen Cursor to load the new MCP configuration.

### 5. Verify Setup

Open an Xcode project, then in Cursor ask:

> "List my open Xcode windows"

Cursor should respond with the available Xcode windows.

## Troubleshooting

**Error: "Tool XcodeListWindows has an output schema but did not return structured content"**

This means you're not using the wrapper. Ensure:
1. The path in `mcp.json` is correct
2. The wrapper is executable: `ls -l ~/bin/mcpbridge-wrapper`
3. Cursor has been restarted after configuration changes

## GUI Configuration (Alternative)

Cursor also supports GUI-based MCP configuration:
1. Open Cursor Settings
2. Navigate to MCP section
3. Add a new stdio server with command: `/Users/YOUR_USERNAME/bin/mcpbridge-wrapper`
