# Claude Code Setup

Configure Claude Code to use Xcode MCP tools via xcodemcpwrapper.

## Configuration Steps

### Option 1: Using uvx (Recommended)

One-line setup:

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

### Option 1B: Using uvx with Web UI (Optional)

Use this variant to enable the dashboard on port `8080`:

```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

### Option 1C: Using Broker Mode (Optional)

`--broker` auto-detects: connects if a daemon is running, spawns one otherwise. Stale socket/PID files from a crashed daemon are cleaned up automatically.

```bash
claude mcp add --transport stdio xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

If you run a dedicated host with `--broker-daemon`, keep clients on `--broker`
so they attach when available and auto-recover when the host is absent.

### Option 2: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
claude mcp add --transport stdio xcode -- /Users/$(whoami)/bin/xcodemcpwrapper
```

### Option 3: Using Local Development (venv)

If you cloned the repo and installed via `make install` in a virtual environment:

```bash
claude mcp add --transport stdio xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

With Web UI:

```bash
claude mcp add --transport stdio xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Replace `/path/to/XcodeMCPWrapper` with the actual path to your cloned repository.

### Migration and Rollback

- Migration: add `--broker` to your `claude mcp add` command.
- Rollback: remove broker flags and re-run the command.

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

**"Could not connect to broker socket ... within 10.0s"**

Broker mode could not reach a ready socket. If using `--broker`, stale files are cleaned up automatically; verify broker status or remove broker flags to return to direct mode.
