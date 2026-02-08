# Getting Started

Get up and running with mcpbridge-wrapper in minutes.

## Prerequisites

1. **Xcode 26.3 or later**
2. **Python 3.7+** (standard on macOS 10.15+)
3. **Enable Xcode Tools MCP Server:**
   - Open **Xcode > Settings** (`⌘,`)
   - Select **Intelligence** in the sidebar
   - Under **Model Context Protocol**, toggle **Xcode Tools** on

## Quick Start

### 1. Install the Wrapper

```bash
# Clone the repository
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd mcpbridge-wrapper

# Run the install script
./scripts/install.sh
```

This installs `mcpbridge-wrapper` to `~/bin/mcpbridge-wrapper`.

### 2. Configure Your MCP Client

#### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper"
    }
  }
}
```

#### Claude Code

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

#### Codex CLI

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/mcpbridge-wrapper
```

### 3. Open Your Project in Xcode

The wrapper operates on whatever Xcode project is currently open:

```bash
open MyApp.xcodeproj
```

### 4. Start Using Xcode MCP Tools

Your AI agent can now use all 20 Xcode MCP tools:

- `XcodeRead` - Read files from the project
- `XcodeWrite` - Write files to the project
- `XcodeUpdate` - Edit files with patches
- `BuildProject` - Build the Xcode project
- `RunAllTests` - Run all tests
- And more...

## Next Steps

- See <doc:Configuration> for detailed configuration options
- See <doc:Troubleshooting> for common issues and solutions
