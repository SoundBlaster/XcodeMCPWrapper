# Architecture Overview

The 1.0 public boundary is stateless MCP `2026-07-28`. The long-lived broker
is a process and ownership optimization, not an MCP protocol session.

## System Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │  xcodemcpwrapper │ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Data Flow

1. **stdin** → modern request boundary validates per-request `_meta`
2. `server/discover` is answered locally; client request IDs are namespaced
3. Broker routes cancellation and progress to the owning client
4. Upstream adapter communicates with Xcode via `mcpbridge` and XPC
5. Responses retain modern result, MRTR, cache, media, and extension fields
6. Missing `structuredContent` is repaired only when the existing compatibility
   rules can do so without rewriting valid structured output
7. **stdout** → Client receives a modern MCP response

## Key Components

### `bridge.py`

- `create_bridge()` - Spawns mcpbridge subprocess
- `forward_stdin()` - Forwards stdin to bridge
- `read_stdout()` - Reads stdout line-by-line
- `cleanup_bridge()` - Handles process termination

### `transform.py`

- `process_response_line()` - Main transformation entry point
- `needs_transformation()` - Detects non-compliant responses
- `extract_text_content()` - Extracts text from content array
- `inject_structured_content()` - Adds structuredContent field

### `__main__.py`

- Sets up stdin/stdout threads
- Runs the main event loop
- Handles cleanup on exit

## Response Transformation

```python
# Input from mcpbridge (non-compliant)
{
  "result": {
    "content": [{"type": "text", "text": '{"status": "ok"}'}]
  }
}

# Output from wrapper (MCP compliant)
{
  "result": {
    "content": [{"type": "text", "text": '{"status": "ok"}'}],
    "structuredContent": {"status": "ok"}
  }
}
```

## Performance

- Line-buffered I/O for minimal latency
- Average overhead: <0.01ms per transformation
- Memory usage: <10MB

## Data Storage

For a full reference on the SQLite metrics database, in-memory collector, and audit log files, see [Data Storage Reference](data-storage.md).
