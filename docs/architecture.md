# Architecture Overview

## System Architecture

```
┌─────────────┐    MCP Protocol    ┌──────────────────┐   MCP Protocol   ┌────────────┐    XPC    ┌─────────┐
│   Cursor    │ ◄────────────────► │  xcodemcpwrapper │ ◄──────────────► │ mcpbridge  │ ◄───────► │  Xcode  │
│ (MCP Client)│                    │  (This Project)  │                  │  (Bridge)  │           │  (IDE)  │
└─────────────┘                    └──────────────────┘                  └────────────┘           └─────────┘
```

## Data Flow

1. **stdin** → Wrapper receives MCP requests from client
2. Wrapper forwards requests unchanged to mcpbridge
3. **mcpbridge** → Communicates with Xcode via XPC
4. **stdout** → mcpbridge returns responses
5. Wrapper detects non-compliant responses (missing `structuredContent`)
6. Wrapper extracts text from `content` array, parses as JSON
7. Wrapper injects `structuredContent` field into response
8. **stdout** → Client receives compliant MCP response

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
