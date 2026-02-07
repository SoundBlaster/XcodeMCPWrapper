# Xcode MCP Wrapper

## Project Overview

This project provides a wrapper solution that enables external AI agents (Cursor, Claude CLI, Codex) to connect to Xcode via the Model Context Protocol (MCP). Xcode 26.3+ includes an MCP bridge (`xcrun mcpbridge`) that exposes Xcode's internal capabilities to MCP clients, but it has a protocol compatibility issue that prevents it from working with strict MCP spec followers like Cursor.

### The Problem

Xcode's `mcpbridge` returns tool responses in the `content` field but omits the required `structuredContent` field when a tool declares an `outputSchema`. According to the MCP specification, when `outputSchema` is declared, responses **must** include `structuredContent`. Claude Code and Codex CLI work because they have special handling for Apple's responses; Cursor strictly follows the spec and rejects non-compliant responses.

### The Solution

A Python wrapper script (`mcpbridge-wrapper`) that intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

## Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge-wrapper│ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Project Structure

```
/
├── AGENTS.md          # This file - project context for AI agents
├── SPECS/
│   ├── Idea.md        # Comprehensive documentation and setup guide
│   └── PRD.md         # Product Requirements Document (currently empty)
```

## Technology Stack

- **Python 3** - Wrapper script implementation
- **Xcode 26.3+** - Required for MCP bridge functionality
- **MCP Protocol** - Model Context Protocol for AI tool integration

## Setup Instructions

### Prerequisites

1. Xcode 26.3 or later
2. Enable Xcode Tools MCP Server:
   - Open **Xcode > Settings** (`⌘,`)
   - Select **Intelligence** in the sidebar
   - Under **Model Context Protocol**, toggle **Xcode Tools** on

### Installation

1. Create the wrapper script at `~/bin/mcpbridge-wrapper`:

```python
#!/usr/bin/env python3
"""
Wrapper for xcrun mcpbridge that adds structuredContent to responses.
"""

import sys
import json
import subprocess
import threading


def process_response(line):
    """Process a single response line from mcpbridge."""
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
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1
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

2. Make it executable:
   ```bash
   chmod +x ~/bin/mcpbridge-wrapper
   ```

3. Configure Cursor to use the wrapper by adding to `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "xcode-tools": {
         "command": "/Users/YOUR_USERNAME/bin/mcpbridge-wrapper"
       }
     }
   }
   ```

## Available Xcode MCP Tools

When properly configured, the following 20 tools become available to AI agents:

### File Operations
- `XcodeRead` - Read files from the project
- `XcodeWrite` - Write files to the project
- `XcodeUpdate` - Edit files with str_replace-style patches
- `XcodeGlob` - Find files by pattern
- `XcodeGrep` - Search file contents
- `XcodeLS` - List directory contents
- `XcodeMakeDir` - Create directories
- `XcodeRM` - Remove files
- `XcodeMV` - Move/rename files

### Build & Test
- `BuildProject` - Build the Xcode project
- `GetBuildLog` - Get build output
- `RunAllTests` - Run all tests
- `RunSomeTests` - Run specific tests
- `GetTestList` - List available tests

### Diagnostics & Navigation
- `XcodeListNavigatorIssues` - Get Xcode issues/errors
- `XcodeRefreshCodeIssuesInFile` - Get live diagnostics
- `XcodeListWindows` - List open Xcode windows

### Advanced Features
- `ExecuteSnippet` - Run code in a REPL-like environment
- `RenderPreview` - Render SwiftUI previews as images
- `DocumentationSearch` - Search Apple docs and WWDC videos

## Usage Guidelines

### How Tools Work

Most tools require a `tabIdentifier` to specify which Xcode window to operate on. The typical flow:

1. **Open your project in Xcode first** (tools operate on whatever is open):
   ```bash
   open MyApp.xcodeproj
   # or
   open MyApp.xcworkspace
   ```

2. The agent automatically:
   - Calls `XcodeListWindows` to discover open windows
   - Gets the `tabIdentifier` (e.g., `windowtab1`) and workspace path
   - Uses that identifier in subsequent tool calls

### Example Workflow

When you ask "build my project":

```
Agent: I'll first need to get the tabIdentifier by listing open Xcode windows.

→ XcodeListWindows()
← { "message": "* tabIdentifier: windowtab1, workspacePath: /Users/you/MyApp.xcodeproj" }

Agent: I see Xcode has MyApp.xcodeproj open. I'll build that.

→ BuildProject({ "tabIdentifier": "windowtab1" })
← { "buildResult": "The project built successfully.", "elapsedTime": 2.17, "errors": [] }
```

## Tool-Specific Notes

### DocumentationSearch

Searches Apple's documentation corpus and WWDC video transcripts using semantic search powered by "Squirrel MLX" (MLX-accelerated embedding system on Apple Silicon). Covers iOS 15 to iOS 26 documentation.

### RenderPreview

Renders SwiftUI previews as actual images that AI agents can analyze. Enables visual UI iteration with AI feedback.

### ExecuteSnippet

Swift REPL-like environment for testing code snippets without creating files or running full builds.

## Environment Variables

- `MCP_XCODE_PID` - (Optional) Manually specify Xcode process ID when auto-detection fails
- `MCP_XCODE_SESSION_ID` - (Optional) UUID identifying an Xcode tool session (rarely needed for external clients)

To get the PID:
```bash
pgrep -x Xcode
```

## Alternative Configuration Methods

### For Claude Code
```bash
claude mcp add --transport stdio xcode -- xcrun mcpbridge
```

### For Codex CLI
```bash
codex mcp add xcode -- xcrun mcpbridge
```

### For Cursor (GUI)
1. Open **Cursor Settings** (`⌘,`)
2. Go to **Features** > **MCP**
3. Click **+ Add New MCP Server**
4. Select **stdio** as the transport type
5. Enter `xcode-tools` as the name
6. Enter the wrapper path as the command

## Security Considerations

- When an external agent connects, Xcode displays a permission dialog showing the agent binary path and PID
- An indicator appears in Xcode when an external tool is connected
- The `mcpbridge` auto-detects the Xcode PID; if multiple Xcode instances are running, it uses `xcode-select` to pick the right one

## Troubleshooting

### Error: "Tool XcodeListWindows has an output schema but did not return structured content"

This means you're not using the wrapper. The wrapper fixes this by adding `structuredContent` to responses.

### Xcode Not Found

Ensure Xcode is running with a project open before the MCP client attempts to connect.

## References

- [Apple Official Documentation](https://developer.apple.com/documentation/xcode/giving-external-agentic-coding-tools-access-to-xcode)
- MCP Protocol Specification
- Xcode 26.3 Release Notes
