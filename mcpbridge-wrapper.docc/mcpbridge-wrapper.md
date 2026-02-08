# ``mcpbridge-wrapper``

A Python wrapper that enables external AI agents to connect to Xcode via the Model Context Protocol (MCP).

## Overview

Xcode 26.3+ includes an MCP bridge (`xcrun mcpbridge`) that exposes Xcode's internal capabilities to MCP clients. However, it has a protocol compatibility issue that prevents it from working with strict MCP spec followers like Cursor.

This wrapper intercepts responses from `xcrun mcpbridge` and copies the data from `content` into `structuredContent`, making Xcode's MCP tools fully compatible with all MCP clients.

## Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge-wrapper│ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

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

## Project Status

**✅ COMPLETE**

| Metric | Value |
|--------|-------|
| Test Coverage | 98.2% |
| Performance Overhead | <0.01ms per transformation |
| Memory Footprint | <10MB |
