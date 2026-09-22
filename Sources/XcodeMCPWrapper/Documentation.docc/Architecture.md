# Architecture

Understanding how the modern MCP `2026-07-28` wrapper works internally.

The public boundary is stateless. The long-lived broker is a process and
ownership optimization, not an MCP protocol session.

## System Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │  xcodemcpwrapper │ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Components

### Protocol Boundary (`protocol.py`)

- Requires per-request `params._meta` with protocol version and client capabilities
- Serves `server/discover` locally
- Preserves modern `resultType`, MRTR continuation state, cache hints, and extensions
- Rejects the legacy `initialize` lifecycle at the public boundary

### Bridge Module (`bridge.py`)

Manages the subprocess connection to `xcrun mcpbridge`:
- Spawns `xcrun mcpbridge` as a subprocess
- Creates bidirectional stdin/stdout pipes
- Uses daemon threads for async I/O
- Handles process lifecycle (startup, shutdown, exit codes)

### Transformation Module (`transform.py`)

The core response transformation logic:
- Detects JSON vs plain text lines
- Identifies non-compliant responses (missing `structuredContent`)
- Extracts text from content arrays
- Parses text as JSON or wraps in fallback structure
- Injects `structuredContent` into results

### Broker Transport (`broker/transport.py`)

- Namespaces request IDs per client session
- Routes cancellation and progress to the owning request
- Acknowledges and filters `subscriptions/listen` events by owner
- Never broadcasts unowned upstream notifications

### Main Entry Point (`__main__.py`)

Orchestrates the flow:
- Sets up the bridge subprocess
- Starts stdin forwarding thread
- Processes stdout lines through transformation
- Outputs transformed responses

## Data Flow

1. **Client → Wrapper:** modern MCP request via stdin
2. **Wrapper:** validates per-request metadata and handles discovery
3. **Wrapper → Broker/Bridge:** namespace ownership and forward the request
4. **Bridge → Xcode:** XPC communication
5. **Xcode → Bridge:** response or progress notification
6. **Wrapper:** restores client IDs and modernizes only missing required envelopes
7. **Wrapper → Client:** modern MCP response via stdout

## Response Transformation

### Input (from Xcode)
```json
{
  "result": {
    "content": [{"type": "text", "text": "{\"status\": \"ok\"}"}]
  }
}
```

### Output (to client)
```json
{
  "result": {
    "content": [{"type": "text", "text": "{\"status\": \"ok\"}"}],
    "structuredContent": {"status": "ok"}
  }
}
```

## Non-Functional Requirements

| Requirement | Target | Achieved |
|-------------|--------|----------|
| Latency overhead | <5ms | ~0.0023ms |
| Memory footprint | <10MB | <10MB |
| Test coverage | ≥90% | 98.2% |

## Data Storage

For a full reference on the SQLite metrics database, in-memory collector, and audit log files, see the [Data Storage Reference](https://github.com/SoundBlaster/XcodeMCPWrapper/blob/main/docs/data-storage.md).

## Technology Stack

- **Python 3.11+** - Wrapper implementation
- **MCP Python SDK v2** - Protocol data models and modern result types
- **asyncio/threads** - Concurrent I/O handling
- **JSON** - Protocol message format
- **XPC** - Xcode internal communication (via mcpbridge)
- **MCP** - Model Context Protocol
