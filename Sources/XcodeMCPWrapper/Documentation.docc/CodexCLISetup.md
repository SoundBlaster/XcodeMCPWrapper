# Codex CLI Setup

Configure Codex CLI to use Xcode MCP tools via xcodemcpwrapper.

## Configuration Steps

### Option 1: Using uvx (Recommended)

One-line setup:

```bash
codex mcp add xcode -- uvx --from mcpbridge-wrapper mcpbridge-wrapper
```

That's it! uvx will automatically download and run the wrapper.

### Option 2: Using Manual Installation

If you installed manually to `~/bin/xcodemcpwrapper`:

```bash
codex mcp add xcode -- /Users/$(whoami)/bin/xcodemcpwrapper
```

### Verify Configuration

```bash
codex mcp list
```

You should see `xcode` in the list.

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
