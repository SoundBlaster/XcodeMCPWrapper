# ``XcodeMCPWrapper``

Connect external MCP clients to Xcode through `xcrun mcpbridge`.

<!-- version-badge:start -->
[![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)](https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.5.0)
<!-- version-badge:end -->

`mcpbridge-wrapper` repairs Xcode tool responses that declare an
`outputSchema` but omit `structuredContent`. Direct mode starts a bridge for
each client. Broker mode shares one persistent upstream bridge among clients
and reduces repeated connection prompts.

## Compatibility

Version 0.5.0 supports Xcode 26.3+ and Xcode 27.0 with MCP clients that use
the legacy `initialize` lifecycle. It does not implement the sessionless MCP
2026-07-28 client protocol. Pin `mcpbridge-wrapper==0.5.0` when configuring
clients that must remain on the legacy protocol.

The wrapper exposes the tool catalog returned by the installed Xcode. On
Xcode 27.0 build `27A266a`, `tools/list` advertised 54 tools, including
`XcodeListWorkspaces`, device interaction, localization, debugger and run
control, build settings, and crash insights. The older `XcodeListWindows` name
was absent. See the [README](https://github.com/SoundBlaster/XcodeMCPWrapper#xcode-270-tools)
for the observed catalog and current client configurations.

## Getting Started

1. Enable **Allow external agents to use Xcode tools** in **Xcode > Settings >
   Intelligence > Model Context Protocol** and open a project in Xcode.
2. Configure your MCP client to run
   `uvx --from 'mcpbridge-wrapper==0.5.0' mcpbridge-wrapper --broker`.
3. Approve the broker host and project folder in Xcode when prompted. A
   successful `tools/list` does not prove that tool calls are authorized.

Check the broker with
`uvx --from 'mcpbridge-wrapper==0.5.0' mcpbridge-wrapper --broker-status`
and Xcode permissions with `xcrun mcp-server status`. See
[Apple's setup guide](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode)
and [Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

## Topics

### Getting Started

- <doc:GettingStarted>
- <doc:Installation>
- <doc:Configuration>

### Supported Clients

- <doc:CursorSetup>
- <doc:ClaudeCodeSetup>
- <doc:CodexCLISetup>

### Reference

- <doc:Troubleshooting>
- <doc:Architecture>
- <doc:EnvironmentVariables>
- <doc:WebUIDashboard>
