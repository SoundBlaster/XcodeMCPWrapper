While digging through Xcode 26.3's internals at 3 AM, I discovered something unusual from Xcode's walled garden that made me genuinely excited: the team built a bridge that lets you use Xcode's AI tools from *any* MCP client.

Not just from Xcode's built-in Claude or Codex agents. From Cursor. From Claude CLI. From anything that speaks MCP.

Apple even has [official documentation](https://developer.apple.com/documentation/xcode/giving-external-agentic-coding-tools-access-to-xcode) for this, but it is does not cover third-party tools like Cursor.

## Prerequisites: Enable Xcode Tools MCP Server

Before any external tool can connect, you need to enable the MCP server in Xcode:

1. Open **Xcode > Settings** (or press `⌘,`)
2. Select **Intelligence** in the sidebar
3. Under **Model Context Protocol**, toggle **Xcode Tools** on

This tells Xcode to accept incoming MCP connections from external agents.

## The mcpbridge

The `xcrun mcpbridge` bridges (pun-intended?) a binary that translates MCP protocol requests into Xcode's internal XPC calls:

```text
┌─────────────┐    MCP Protocol    ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └────────────┘           └─────────┘
```

Xcode must be running with a project open for this to work. The bridge connects to Xcode's process and exposes all 20 of its native MCP tools.

## Claude Code and Codex CLI

Apple provides official one-liner commands for Claude Code and Codex. For **Claude Code**, run:

```bash
claude mcp add --transport stdio xcode -- xcrun mcpbridge
```

For **Codex**, run:

```bash
codex mcp add xcode -- xcrun mcpbridge
```

To verify the configuration worked:

```bash
claude mcp list
# or
codex mcp list
```

That is all you need for the official CLI tools. But what about Cursor or other VS Code forks?

## Setting Up in Cursor

There are three ways to add xcode-tools to Cursor, from easiest to most manual:

### Option 1: One-Click Install

Click this link to install xcode-tools directly:

**[Add xcode-tools to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=xcode-tools&config=eyJjb21tYW5kIjoieGNydW4iLCJhcmdzIjpbIm1jcGJyaWRnZSJdfQo=)**

Cursor will prompt you to confirm the installation. Click "Install" and you are done.

### Option 2: GUI

1. Open **Cursor Settings** (⌘,)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter `xcode-tools` as the name
6. Enter `xcrun mcpbridge` as the command

### Option 3: JSON Config

Add this to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "xcrun",
      "args": ["mcpbridge"]
    }
  }
}
```

The `mcpbridge` **auto-detects the Xcode PID**. You do not need to specify it.

## Known Limitation in Xcode 26.3 RC (and the Fix)

If you try using xcode-tools in Cursor with the basic configuration above, you may encounter this error:

```
MCP error -32600: Tool XcodeListWindows has an output schema but did not return structured content
```

This is a known limitation in Xcode 26.3 RC. According to the MCP specification, when a tool declares an `outputSchema`, the response **must** include a `structuredContent` field. Apple's `mcpbridge` returns the data in `content` but not in `structuredContent`.

Claude Code and Codex work because they have special handling for Apple's responses (likely due to Apple's partnership). Cursor strictly follows the MCP spec and rejects the non-compliant responses.

### The Wrapper Fix

Wrap `mcpbridge` with a script that copies `content` into `structuredContent`. Create this file at `~/bin/mcpbridge-wrapper`:

```python
#!/usr/bin/env python3
"""
Wrapper for xcrun mcpbridge that adds structuredContent to responses.
"""

import sys, json, subprocess, threading

def process_response(line):
    try:
        data = json.loads(line)
        if isinstance(data, dict) and 'result' in data:
            result = data['result']
            if isinstance(result, dict):
                if 'content' in result and 'structuredContent' not in result:
                    content = result.get('content', [])
                    if isinstance(content, list) and len(content) > 0:
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                text = item.get('text', '')
                                try:
                                    result['structuredContent'] = json.loads(text)
                                except json.JSONDecodeError:
                                    result['structuredContent'] = {"text": text}
                                break
        return json.dumps(data)
    except json.JSONDecodeError:
        return line

def main():
    proc = subprocess.Popen(
        ['xcrun', 'mcpbridge'] + sys.argv[1:],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=sys.stderr, text=True, bufsize=1
    )
    
    def pipe_output(stdout):
        for line in stdout:
            print(process_response(line.strip()), flush=True)
    
    threading.Thread(target=pipe_output, args=(proc.stdout,), daemon=True).start()
    
    for line in sys.stdin:
        proc.stdin.write(line)
        proc.stdin.flush()

if __name__ == '__main__':
    main()
```

Make it executable:

```bash
chmod +x ~/bin/mcpbridge-wrapper
```

Then update your `~/.cursor/mcp.json` to use the wrapper:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper"
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual username. Now Cursor can use all 20 xcode-tools!

The auto-detection logic:
1. If exactly one Xcode process is running, it connects to that
2. If multiple Xcode instances are running, it uses `xcode-select` to pick the right one
3. If Xcode is not running, it exits with an error

Restart Cursor (or reload the window), and you should see the `xcode-tools` server appear in your MCP tools list.

## The Permission Dialog

When the MCP client first tries to connect, Xcode will ask for permission. Click "Allow" and you are good to go. This is Apple's way of ensuring you explicitly grant access to Xcode's capabilities. The dialog shows the exact path to the agent binary and its PID.

## The Xcode MCP Tools

Here is everything you get access to in the Xcode 26.3 MCP tools:

- `XcodeRead` - Read files from the project
- `XcodeWrite` - Write files to the project
- `XcodeUpdate` - Edit files with str_replace-style patches
- `XcodeGlob` - Find files by pattern
- `XcodeGrep` - Search file contents
- `XcodeLS` - List directory contents
- `XcodeMakeDir` - Create directories
- `XcodeRM` - Remove files
- `XcodeMV` - Move/rename files
- `BuildProject` - Build the Xcode project
- `GetBuildLog` - Get build output
- `RunAllTests` - Run all tests
- `RunSomeTests` - Run specific tests
- `GetTestList` - List available tests
- `XcodeListNavigatorIssues` - Get Xcode issues/errors
- `XcodeRefreshCodeIssuesInFile` - Get live diagnostics
- `ExecuteSnippet` - Run code in a REPL-like environment
- `RenderPreview` - Render SwiftUI previews as images
- `DocumentationSearch` - Search Apple docs and WWDC videos
- `XcodeListWindows` - List open Xcode windows

## How the Tools Work

Most tools require a `tabIdentifier` to specify which Xcode window to operate on. The agent handles this automatically:

1. **Open your project in Xcode** first (the tools operate on whatever is open):

```bash
open MyApp.xcodeproj
# or
open MyApp.xcworkspace
```

2. **Ask the agent to do something** like "build my project"

3. **The agent automatically**:
   - Calls `XcodeListWindows` to discover open windows
   - Gets the `tabIdentifier` (e.g., `windowtab1`) and workspace path
   - Uses that identifier in the actual tool call

Here is what that looks like in practice when you ask "build my project":

```
Agent: I'll first need to get the tabIdentifier by listing open Xcode windows.

→ XcodeListWindows()
← { "message": "* tabIdentifier: windowtab1, workspacePath: /Users/you/MyApp.xcodeproj" }

Agent: I see Xcode has MyApp.xcodeproj open. I'll build that.

→ BuildProject({ "tabIdentifier": "windowtab1" })
← { "buildResult": "The project built successfully.", "elapsedTime": 2.17, "errors": [] }
```

## DocumentationSearch

This searches Apple's entire documentation corpus *and* WWDC video transcripts. The semantic search is powered by what Apple internally calls "Squirrel MLX", their MLX-accelerated embedding system optimized for Apple Silicon.

When you ask about a framework, it can pull relevant context from WWDC sessions you might have missed. The search covers everything from iOS 15 to iOS 26 documentation, all indexed and searchable semantically.

### RenderPreview

This renders your SwiftUI previews and returns actual images. Your AI agent can literally *see* what your UI looks like. Ask it to tweak a color, it can verify the change visually.

This is something no other IDE offers to external agents. The agent can iterate on UI changes with visual feedback.

### ExecuteSnippet

A Swift REPL-like environment. Test code snippets without creating a file or running a full build. Great for quickly validating logic or testing API calls.

## Adding Context with AGENTS.md

Apple recommends adding hints about Xcode and your project to configuration files like `AGENTS.md` or `CLAUDE.md` in your project root. This helps the agent understand your project structure:

```markdown
# Project Context

## Build System
- This is an iOS 26 SwiftUI project
- Use `BuildProject` to compile, not shell commands
- SwiftUI previews available via `RenderPreview`

## Testing
- Run tests with `RunAllTests` or `RunSomeTests`
- Test results available via Xcode's test navigator

## Documentation
- Use `DocumentationSearch` to find Apple API docs
- WWDC session transcripts are searchable
```

## Manual PID Configuration (Edge Cases)

In rare cases where auto-detection does not work (e.g., running multiple Xcode versions simultaneously), you can manually specify which Xcode to connect to:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "xcrun",
      "args": ["mcpbridge"],
      "env": {
        "MCP_XCODE_PID": "12345"
      }
    }
  }
}
```

To get the PID:

```bash
pgrep -x Xcode
```

The PID stays the same as long as Xcode is running.

## Session ID (Advanced)

The mcpbridge also accepts an optional `MCP_XCODE_SESSION_ID` environment variable described as "a UUID identifying an Xcode tool session." Xcode generates these automatically for its internal agents (you can see them in `~/Library/Developer/Xcode/CodingAssistant/codex/config.toml`).

For external clients like Cursor, I have not found a scenario where you would need to set this manually as the auto-detection works fine without it.

## Xcode Alerts

When an external agent connects to Xcode, you will see an indicator in Xcode showing that an external tool is connected and active. This is a nice touch for security awareness as you always know when something or who is accessing your project.

## Customizing Xcode's Built-in Agents

If you want to customize the Codex or Claude agents that run *inside* Xcode (not external ones), you can use configuration files in:

- **Codex**: `~/Library/Developer/Xcode/CodingAssistant/codex/`
- **Claude Agent**: `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/`

These mirror the standard `.codex` and `.claude` configuration directories but are kept separate so Xcode does not interere  withyour existing configurations.

## What's Next

You can build workflows that combine Xcode's native capabilities (building, testing, previewing) with other MCP servers like Figma for design-to-code pipelines.

The fact that Apple exposed this as a standard MCP interface rather than keeping it locked to their own agents suggests they want the ecosystem to integrate with Xcode in new ways. The [official documentation](https://developer.apple.com/documentation/xcode/giving-external-agentic-coding-tools-access-to-xcode) even encourages it.

I am curious to see what workflows people build with this. If you create something interesting, let me know on [X](https://x.com/rudrank)!

Happy Xcoding!
