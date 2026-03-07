# Codex CLI Setup

Configure Codex CLI to use Xcode MCP tools via xcodemcpwrapper.

## Configuration Steps

### Option 1: Using uvx (Recommended)

One-line setup:

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

### Option 1B: Using uvx with Web UI (Optional)

Use this variant to enable the dashboard on port `8080`:

```bash
codex mcp add xcode -- uvx --from 'mcpbridge-wrapper[webui]' mcpbridge-wrapper --web-ui --web-ui-port 8080
```

### Option 1C: Using Broker Mode (Optional)

`--broker` auto-detects: connects if a daemon is running, spawns one otherwise. Stale socket/PID files from a crashed daemon are cleaned up automatically.

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper --broker
```

If you run a dedicated host with `--broker-daemon`, keep clients on `--broker`
so they attach when available and auto-recover when the host is absent.

### Option 2: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
codex mcp add xcode -- /Users/$(whoami)/bin/xcodemcpwrapper
```

### Option 3: Using Local Development (venv)

If you cloned the repo and installed via `make install` in a virtual environment:

```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper
```

With Web UI:

```bash
codex mcp add xcode -- /path/to/XcodeMCPWrapper/.venv/bin/mcpbridge-wrapper --web-ui --web-ui-port 8080
```

Replace `/path/to/XcodeMCPWrapper` with the actual path to your cloned repository.

### Migration and Rollback

- Migration: add `--broker` to your `codex mcp add` command.
- Rollback: remove broker flags and re-run the command.

### Verify Configuration

```bash
codex mcp list
```

You should see `xcode` in the list.

If you keep more than one editor on `--broker`, use the shared-daemon checks in
<doc:Troubleshooting> to confirm both editors attach to the same host instead
of spawning separate owners.

## Usage

Once configured, you can use Codex CLI with Xcode:

```bash
codex "Build my Xcode project"
```

Codex will automatically:
1. Discover open Xcode windows
2. Build the project
3. Report results

## Example Session

```bash
$ codex "Run all tests"

I'll run all tests in your Xcode project. Let me first check what windows are open.

→ XcodeListWindows()
← { "message": "* tabIdentifier: windowtab1, workspacePath: /Users/you/MyApp.xcodeproj" }

Found MyApp.xcodeproj. Running all tests now.

→ RunAllTests({ "tabIdentifier": "windowtab1" })
← { "testResult": "All tests passed", "passed": 42, "failed": 0 }

✓ All 42 tests passed!
```

## Removing the Server

```bash
codex mcp remove xcode
```

## Additional Options

Codex CLI supports additional configuration:

```bash
# View detailed MCP configuration
codex mcp list --verbose

# Test the MCP connection
codex mcp test xcode
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
