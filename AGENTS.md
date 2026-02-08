# Xcode MCP Wrapper

## Project Overview

This project provides a wrapper solution that enables external AI agents (Cursor, Claude CLI, Codex) to connect to Xcode via the Model Context Protocol (MCP). Xcode 26.3+ includes an MCP bridge (`xcrun mcpbridge`) that exposes Xcode's internal capabilities to MCP clients, but it has a protocol compatibility issue that prevents it from working with strict MCP spec followers like Cursor.

### The Problem

Xcode's `mcpbridge` returns tool responses in the `content` field but omits the required `structuredContent` field when a tool declares an `outputSchema`. According to the MCP specification, when `outputSchema` is declared, responses **must** include `structuredContent`. Claude Code and Codex CLI work because they have special handling for Apple's responses; Cursor strictly follows the spec and rejects non-compliant responses.

### The Solution

A Python wrapper (`xcodemcpwrapper`) that intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

## Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │  xcodemcpwrapper │ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Project Status

**✅ COMPLETE - 2026-02-08**

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Foundation & Scaffolding | 6/6 | ✅ Complete |
| Phase 2: Core Bridge Implementation | 7/7 | ✅ Complete |
| Phase 3: Response Transformation Engine | 10/10 | ✅ Complete |
| Phase 4: Edge Case Handling | 9/9 | ✅ Complete |
| Phase 5: Testing & Verification | 14/14 | ✅ Complete |
| Phase 6: Packaging & Distribution | 8/8 | ✅ Complete |
| Phase 7: Documentation | 11/11 | ✅ Complete |
| Phase 8: Documentation Publishing | 2/2 | ✅ Complete |
| **Total** | **67/67** | **✅ 100%** |

### Metrics

- **Test Coverage:** 98.2%
- **Performance:** <0.01ms overhead per transformation (0.0023ms avg)
- **Memory:** <10MB footprint
- **Lines of Code:** ~400 Python + 2000+ lines documentation

## Project Structure

```
/
├── AGENTS.md              # This file - project context for AI agents
├── README.md              # Main project README
├── CHANGELOG.md           # Version history
├── pyproject.toml         # Python package configuration
├── Makefile               # Common development tasks
├── scripts/
│   ├── install.sh         # Installation script
│   ├── pick_next_task.py  # Task selection helper
│   └── calc_progress.py   # Progress calculator
├── src/mcpbridge_wrapper/
│   ├── __init__.py        # Package init
│   ├── __main__.py        # Main entry point
│   ├── bridge.py          # Subprocess bridge management
│   ├── transform.py       # Response transformation engine
│   └── cli.py             # CLI entry point
├── tests/
│   ├── unit/              # Unit tests (181+ tests)
│   │   ├── test_bridge.py
│   │   ├── test_transform.py
│   │   ├── test_main.py
│   │   └── conftest.py
│   └── integration/       # Integration tests
│       ├── test_e2e.py
│       └── test_performance.py
├── config/                # Configuration templates
│   ├── cursor-mcp.json
│   ├── claude-code.txt
│   └── codex-cli.txt
├── docs/                  # Documentation
│   ├── installation.md
│   ├── cursor-setup.md
│   ├── claude-setup.md
│   ├── codex-setup.md
│   ├── troubleshooting.md
│   ├── architecture.md
│   └── tools-reference.md
└── SPECS/                 # Specifications and task tracking
    ├── Workplan.md        # Master task tracker (65 tasks)
    ├── COMMANDS/          # Workflow commands
    ├── ARCHIVE/           # Completed task artifacts (65 archived)
    └── INPROGRESS/        # Current task tracking
```

## Technology Stack

- **Python 3.7+** - Wrapper implementation (tested on 3.10.19)
- **Xcode 26.3+** - Required for MCP bridge functionality
- **MCP Protocol** - Model Context Protocol for AI tool integration
- **pytest** - Testing framework (98%+ coverage)
- **ruff** - Linting and formatting
- **mypy** - Type checking

## Quick Start

### Prerequisites

1. Xcode 26.3 or later
2. Enable Xcode Tools MCP Server:
   - Open **Xcode > Settings** (`⌘,`)
   - Select **Intelligence** in the sidebar
   - Under **Model Context Protocol**, toggle **Xcode Tools** on

### Installation

```bash
# Clone the repository
git clone https://github.com/SoundBlaster/XcodeMCPWrapper.git
cd XcodeMCPWrapper

# Run the install script
./scripts/install.sh
```

### Configuration

#### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper"
    }
  }
}
```

#### Claude Code

```bash
claude mcp add --transport stdio xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
```

#### Codex CLI

```bash
codex mcp add xcode -- /Users/YOUR_USERNAME/bin/xcodemcpwrapper
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

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test modules
pytest tests/unit/test_transform.py
pytest tests/integration/test_performance.py

# Run linting
ruff check src/

# Run type checking
mypy src/
```

### Verified with Real Xcode

Tested successfully with real `xcrun mcpbridge`:

```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | python -m mcpbridge_wrapper
```

Result: Wrapper correctly transforms responses by adding `structuredContent` field.

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

## Troubleshooting

### Error: "Tool XcodeListWindows has an output schema but did not return structured content"

This means you're not using the wrapper. The wrapper fixes this by adding `structuredContent` to responses.

### Xcode Not Found

Ensure Xcode is running with a project open before the MCP client attempts to connect.

For more troubleshooting tips, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Documentation

- [Installation Guide](docs/installation.md)
- [Cursor Setup](docs/cursor-setup.md)
- [Claude Code Setup](docs/claude-setup.md)
- [Codex CLI Setup](docs/codex-setup.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Architecture Overview](docs/architecture.md)
- [Tools Reference](docs/tools-reference.md)
- [Usage Examples](docs/usage-examples.md)

## Contributing

### Contribution Workflow

**⚠️ IMPORTANT:** The `main` branch is protected by GitHub ruleset. **All contributions must be made through Pull Requests (PRs).**

Direct pushes to `main` are not allowed. Follow this workflow:

1. **Create a feature branch from main:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. **Push the branch to origin:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub:
   - Go to https://github.com/SoundBlaster/XcodeMCPWrapper/pulls
   - Click "New Pull Request"
   - Select your feature branch and compare against `main`
   - Fill in the PR template with description of changes
   - Request review if applicable

5. **After PR is merged**, clean up locally:
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/your-feature-name
   ```

### Code Quality Requirements

Before submitting a PR, ensure:
- All tests pass: `pytest`
- Code coverage remains ≥90%: `pytest --cov`
- Linting passes: `ruff check src/`
- Type checking passes: `mypy src/`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup and quality gate commands.

## References

- [Apple Official Documentation](https://developer.apple.com/documentation/xcode/giving-external-agentic-coding-tools-access-to-xcode)
- MCP Protocol Specification
- Xcode 26.3 Release Notes
