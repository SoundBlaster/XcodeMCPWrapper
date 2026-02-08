# Xcode MCP Tools Reference

The following 20 tools become available when using mcpbridge-wrapper with Xcode:

## File Operations

| Tool | Description |
|------|-------------|
| `XcodeRead` | Read files from the project |
| `XcodeWrite` | Write files to the project |
| `XcodeUpdate` | Edit files with str_replace-style patches |
| `XcodeGlob` | Find files by pattern |
| `XcodeGrep` | Search file contents |
| `XcodeLS` | List directory contents |
| `XcodeMakeDir` | Create directories |
| `XcodeRM` | Remove files |
| `XcodeMV` | Move/rename files |

## Build & Test

| Tool | Description |
|------|-------------|
| `BuildProject` | Build the Xcode project |
| `GetBuildLog` | Get build output |
| `RunAllTests` | Run all tests |
| `RunSomeTests` | Run specific tests |
| `GetTestList` | List available tests |

## Diagnostics & Navigation

| Tool | Description |
|------|-------------|
| `XcodeListNavigatorIssues` | Get Xcode issues/errors |
| `XcodeRefreshCodeIssuesInFile` | Get live diagnostics |
| `XcodeListWindows` | List open Xcode windows |

## Advanced Features

| Tool | Description |
|------|-------------|
| `ExecuteSnippet` | Run code in a REPL-like environment |
| `RenderPreview` | Render SwiftUI previews as images |
| `DocumentationSearch` | Search Apple docs and WWDC videos |

## Usage

Most tools require a `tabIdentifier` to specify which Xcode window to operate on. The typical flow:

1. Call `XcodeListWindows` to discover open windows
2. Get the `tabIdentifier` (e.g., `windowtab1`) and workspace path
3. Use that identifier in subsequent tool calls
