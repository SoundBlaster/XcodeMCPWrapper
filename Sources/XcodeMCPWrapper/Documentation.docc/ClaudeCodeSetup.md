# Claude Code Setup

Configure Claude Code to use Xcode MCP tools via xcodemcpwrapper.

## Configuration Steps

### Option 1: Using uvx (Recommended)

One-line setup:

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

### Option 2: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
claude mcp add --transport stdio xcode -- /Users/$(whoami)/bin/xcodemcpwrapper
```

### Verify Configuration

```bash
claude mcp list
```

You should see `xcode` in the list with transport `stdio`.

## Usage

Once configured, you can ask Claude Code to:

```
Build my Xcode project
```

Claude will:
1. Call `XcodeListWindows` to find open Xcode projects
2. Get the `tabIdentifier`
3. Call `BuildProject` with the identifier

## Example Session

```
$ claude
> Build my project

I'll help you build your Xcode project. Let me first check what Xcode windows are open.

→ XcodeListWindows()
← { "message": "* tabIdentifier: windowtab1, workspacePath: /Users/you/MyApp.xcodeproj" }

I see you have MyApp.xcodeproj open. I'll build that now.

→ BuildProject({ "tabIdentifier": "windowtab1" })
← { "buildResult": "The project built successfully.", "elapsedTime": 2.17, "errors": [] }

✓ Build completed successfully in 2.17 seconds with no errors.
```

## Removing the Server

```bash
claude mcp remove xcode
```

## Troubleshooting

**"command not found: uvx"**

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

**"Found 0 tools"**

Make sure Xcode Tools MCP is enabled in Xcode:
1. Open **Xcode** > **Settings** (`⌘,`)
2. Select **Intelligence**
3. Toggle **Xcode Tools** ON
