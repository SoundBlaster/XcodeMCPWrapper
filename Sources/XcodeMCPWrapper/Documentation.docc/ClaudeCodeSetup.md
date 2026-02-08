# Claude Code Setup

Configure Claude Code to use Xcode MCP tools via mcpbridge-wrapper.

## Configuration Steps

### 1. Install mcpbridge-wrapper

```bash
./scripts/install.sh
```

### 2. Add MCP Server

```bash
claude mcp add --transport stdio xcode -- /Users/$(whoami)/bin/mcpbridge-wrapper
```

### 3. Verify Configuration

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
