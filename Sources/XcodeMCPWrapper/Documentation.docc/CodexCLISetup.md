# Codex CLI Setup

Configure Codex CLI to use Xcode MCP tools via xcodemcpwrapper.

## Configuration Steps

### 1. Install xcodemcpwrapper

```bash
./scripts/install.sh
```

### 2. Add MCP Server

```bash
codex mcp add xcode -- /Users/$(whoami)/bin/xcodemcpwrapper
```

### 3. Verify Configuration

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
