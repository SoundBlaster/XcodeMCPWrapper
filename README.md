# Xcode MCP Bridge Wrapper

<!-- mcp-name: io.github.SoundBlaster/xcode-mcpbridge-wrapper -->

<!-- version-badge:start -->
[![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)](https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.5.0)
<!-- version-badge:end -->
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`mcpbridge-wrapper` connects external MCP clients to Xcode through Apple's
`xcrun mcpbridge`. It repairs Xcode tool responses that declare an
`outputSchema` but omit `structuredContent`. The repair works in both direct
and broker modes. Broker mode also lets several clients share one persistent
Xcode connection, reducing repeated connection prompts.

## Compatibility

| Component | Support in 0.5.0 |
| --- | --- |
| Xcode | 26.3+ and **27.0** on macOS; Xcode 27.0 handshake and tool discovery verified |
| MCP clients | Clients using the `initialize` lifecycle; check the protocol used by your client version |
| MCP 2026-07-28 | Not supported by 0.5.0; the sessionless implementation remains experimental on a separate branch |
| Python | 3.9-3.12; `uvx` manages its own environment |

The wrapper does **not** bundle Xcode tools. It exposes the catalog returned by
the installed Xcode, so tool names and availability can change with Xcode
updates and permissions. The Xcode 27.0 catalog observed with build `27A266a`
is listed [below](#xcode-270-tools).

## Quick Start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
   Xcode 26.3 or newer. Xcode 27.0 is supported.
2. In **Xcode > Settings > Intelligence > Model Context Protocol**, enable
   **Allow external agents to use Xcode tools**. Open the project you want to
   use in Xcode. See [Apple's setup guide](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode).
3. Add one of the client configurations below. Pin `0.5.0` to keep the legacy
   MCP contract when a future major release becomes available.
4. Start the client and approve the Xcode access prompt if shown. After
   approval, reload or reconnect the MCP server in the client so it fetches
   `tools/list` again, then verify with a real Xcode tool call. A green MCP
   indicator alone only confirms the handshake.

Broker mode is recommended for multiple clients. All examples use the same
per-user daemon. The first client starts it; subsequent clients reuse it.

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper==0.5.0", "mcpbridge-wrapper", "--broker"]
    }
  }
}
```

### Codex

Add to `~/.codex/config.toml` and restart Codex:

```toml
[mcp_servers.xcode-tools]
command = "uvx"
args = ["--from", "mcpbridge-wrapper==0.5.0", "mcpbridge-wrapper", "--broker"]
```

### Zed

Add inside `~/.config/zed/settings.json` under the top-level
`context_servers` key, then disable and re-enable the server in
**Settings > AI > MCP Servers**:

```json
{
  "context_servers": {
    "xcode-tools": {
      "command": "uvx",
      "args": ["--from", "mcpbridge-wrapper==0.5.0", "mcpbridge-wrapper", "--broker"],
      "env": {}
    }
  }
}
```

See [Zed's MCP configuration guide](https://zed.dev/docs/ai/mcp) for the
settings UI and server status indicator.

### Claude Code

```bash
claude mcp add --transport stdio xcode -- uvx --from 'mcpbridge-wrapper==0.5.0' mcpbridge-wrapper --broker
```

For a single client that does not need the shared daemon, remove `--broker`
from its command to use direct mode. Manual installation and Web UI options
are covered in the [installation](docs/installation.md),
[broker](docs/broker-mode.md), and [Web UI](docs/webui-setup.md) guides.

## Xcode 27.0 Approval and Verification

Xcode 27.0 may ask for permission for the **broker host process** and for the
project folder. The prompt identifies the Python executable and PID, not the
editor name. A new `uvx` host identity may need a fresh approval even if an
older Python installation was already permitted. Approve access only when the
path and project are expected.

If a tool reports that the agent is not approved, use `XcodeOpenWorkspace`
with the absolute path of an existing `.xcodeproj` or `.xcworkspace` to
request access, approve the prompt in Xcode, then retry the read-only tool.
Do not treat a successful `tools/list` or a green client status dot as proof
that Xcode tool calls are authorized. Check Xcode's state with:

```bash
xcrun mcp-server status
uvx --from 'mcpbridge-wrapper==0.5.0' mcpbridge-wrapper --broker-status
```

The second command should show `Proxy version: 0.5.0` and `Daemon version:
0.5.0`. If an older daemon is still running, stop it once and reconnect the
clients:

```bash
uvx --from 'mcpbridge-wrapper==0.5.0' mcpbridge-wrapper --broker-stop
```

Stopping the singleton temporarily disconnects every client using it. The
next `--broker` connection starts a new daemon. For a stable long-lived host
identity, see the [dedicated broker host](docs/broker-mode.md#dedicated-host-frontend-workflow).

## Xcode 27.0 Tools

`tools/list` exposed **54 tools** on Xcode 27.0 build `27A266a` during a
local smoke test. This is an observed catalog, not a hard-coded wrapper API.
Xcode 27 adds workspace creation/opening, simulator interaction, run and
debugger control, build configuration, localization, and crash/field insight
tools. See [Apple's Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

- **Workspaces and targets:** `XcodeListWorkspaces`, `XcodeOpenWorkspace`,
  `XcodeCloseWorkspace`, `XcodeNewProject`, `XcodeNewTarget`,
  `XcodeListTargets`, `XcodeListTemplates`, `XcodeListSchemes`,
  `XcodeSwitchScheme`, `XcodeListRunDestinations`,
  `XcodeSwitchRunDestination`, `XcodeListTestPlans`, `XcodeSwitchTestPlan`.
- **Files and diagnostics:** `XcodeRead`, `XcodeWrite`, `XcodeUpdate`,
  `XcodeLS`, `XcodeGlob`, `XcodeGrep`, `XcodeMakeDir`, `XcodeMV`, `XcodeRM`,
  `XcodeRefreshCodeIssuesInFile`.
- **Build, test, run, and debug:** `BuildProject`, `GetBuildLog`,
  `GetTestList`, `RunAllTests`, `RunSomeTests`, `RunProject`, `StopProject`,
  `GetConsoleOutput`, `InvokeDebuggerCommand`, `GetFileCompilerFlags`,
  `UpdateFileCompilerFlags`, `GetTargetBuildSettings`,
  `UpdateTargetBuildSetting`.
- **Device interaction:** `DeviceInteractionStartSession`,
  `DeviceInteractionStartWorkspaceSession`, `DeviceInteractionInstallAndRun`,
  `DeviceInteractionSynthesize`, `DeviceInteractionEndSession`.
- **Localization:** `LocalizationPlanner`, `StringCatalogContext`,
  `StringCatalogRead`, `StringCatalogEdit`.
- **Crash and field insights:** `GetTopCrashIssues`, `GetCrashIssueLogs`,
  `GetTopFieldPerformanceIssues`, `GetFieldPerformanceIssueLogs`.
- **Previews and reference:** `RenderPreview`, `DocumentationSearch`,
  `RunCodeSnippet`.
- **Project metadata:** `AddEntitlement`, `AddInfoPlist`.

In this catalog, the older `XcodeListWindows` name is absent; use
`XcodeListWorkspaces` to inspect workspaces after Xcode approval. Tool calls
such as builds, file edits, and device interaction can change project or
device state. Start with read-only calls when validating a new setup.

## Development

For source installation and quality gates, see [Contributing](CONTRIBUTING.md).
The package is also available on [PyPI](https://pypi.org/project/mcpbridge-wrapper/0.5.0/)
and in the [MCP Registry](https://registry.modelcontextprotocol.io/?q=io.github.SoundBlaster%2Fxcode-mcpbridge-wrapper).

Licensed under the [MIT License](LICENSE).
