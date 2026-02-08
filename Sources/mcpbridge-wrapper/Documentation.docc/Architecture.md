# Architecture

Understanding how mcpbridge-wrapper works internally.

## System Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │ mcpbridge-wrapper│ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Components

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

### Main Entry Point (`__main__.py`)

Orchestrates the flow:
- Sets up the bridge subprocess
- Starts stdin forwarding thread
- Processes stdout lines through transformation
- Outputs transformed responses

## Data Flow

1. **Client → Wrapper:** MCP request via stdin
2. **Wrapper → Bridge:** Forward unmodified to mcpbridge
3. **Bridge → Xcode:** XPC communication
4. **Xcode → Bridge:** XPC response
5. **Bridge → Wrapper:** MCP response (non-compliant)
6. **Wrapper Transform:** Add `structuredContent` field
7. **Wrapper → Client:** Compliant MCP response via stdout

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

## Technology Stack

- **Python 3.7+** - Wrapper implementation
- **asyncio/threads** - Concurrent I/O handling
- **JSON** - Protocol message format
- **XPC** - Xcode internal communication (via mcpbridge)
- **MCP** - Model Context Protocol
