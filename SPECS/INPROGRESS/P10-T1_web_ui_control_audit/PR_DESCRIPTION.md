# P10-T1: Web UI Control & Audit Dashboard

## Summary

This PR introduces **Phase 10: Web UI Control & Audit Dashboard** - a new feature that provides a web-based interface for real-time monitoring, control, and audit logging of the XcodeMCPWrapper.

## Problem

Currently, the XcodeMCPWrapper operates as a black-box stdio bridge. Users have no visibility into:
- Which MCP tools are being called and how frequently
- Request/response latency and performance metrics
- Error rates and failure patterns
- Active connections and concurrent operations
- Historical audit trail of tool invocations

## Solution

A lightweight web dashboard that exposes operational metrics and provides control capabilities through a clean, modern interface.

### Key Features

1. **Real-time Metrics Dashboard**
   - Live RPS counter, latency percentiles (p50, p95, p99)
   - Error rate tracking
   - Active connections display
   - WebSocket updates every second

2. **Tool Usage Analytics**
   - Bar chart of top 10 most used tools
   - Pie chart by tool categories
   - Timeline graphs (1h, 24h, 7d views)
   - Success/failure rates per tool

3. **Request/Response Inspector**
   - Live log stream of recent tool calls
   - Search/filter by tool name, status, time range
   - Expandable JSON detail view
   - Export to JSON/CSV

4. **Audit Logging**
   - Persistent structured logs of all MCP interactions
   - Configurable log rotation (default: 30 days)
   - Compliance-ready audit trail

5. **Control Interface**
   - Service status indicator
   - Configuration viewer (read-only)
   - Environment display (sanitized)

## Architecture

```
┌─────────────────┐     HTTP/WebSocket     ┌──────────────────┐    stdio    ┌────────────┐
│   Web Browser   │ ◄────────────────────► │  Web UI Server   │ ◄─────────► │  Wrapper   │
│  (Dashboard)    │                        │  (FastAPI/Flask) │             │  Core      │
└─────────────────┘                        └──────────────────┘             └─────┬──────┘
                                                                                  │
                                                                                  ▼
                                                                          ┌──────────────┐
                                                                          │  mcpbridge   │
                                                                          └──────────────┘
```

## Files Added/Modified

### New Files
- `SPECS/PRD/P10-T1_web_ui_control_audit.md` - Product Requirements Document
- `SPECS/INPROGRESS/P10-T1_web_ui_control_audit/` - Task tracking directory
- `SPECS/Workplan.md` - Updated with Phase 10 section

### Implementation Files (To Be Added in Future Commits)
- `src/mcpbridge_wrapper/webui/` - Web UI package
- `config/webui.json` - Configuration template
- `docs/webui-setup.md` - Documentation
- `tests/unit/webui/` - Unit tests
- `tests/integration/webui/` - Integration tests

## Usage

```bash
# Enable Web UI via command line
xcodemcpwrapper --web-ui --web-ui-port 8080

# Or via environment variables
export MCP_WRAPPER_WEB_UI=true
export MCP_WRAPPER_WEB_UI_PORT=8080
xcodemcpwrapper
```

Then open `http://localhost:8080` in your browser.

## Configuration

```json
{
  "enabled": false,
  "host": "127.0.0.1",
  "port": 8080,
  "auth": {
    "enabled": false,
    "type": "basic",
    "username": "admin"
  },
  "metrics": {
    "retention_seconds": 86400,
    "update_interval_ms": 1000
  },
  "audit": {
    "enabled": true,
    "log_path": "~/.xcodemcpwrapper/audit.log",
    "rotation_days": 30,
    "max_size_mb": 100
  }
}
```

## Acceptance Criteria

- [ ] Dashboard loads at `http://localhost:8080` when enabled
- [ ] Real-time metrics update every second via WebSocket
- [ ] Tool usage charts display accurate data
- [ ] Audit logs capture all MCP tool calls
- [ ] Log export produces valid JSON/CSV files
- [ ] Web UI has < 1% performance impact on wrapper
- [ ] All existing tests pass with Web UI enabled
- [ ] New unit tests achieve > 90% coverage for webui module
- [ ] Documentation updated with Web UI setup instructions

## Dependencies

Optional dependencies (only loaded when webui is enabled):
- `fastapi>=0.100.0`
- `uvicorn>=0.23.0`
- `websockets>=11.0`
- `python-multipart>=0.0.6`

## Testing

```bash
# Run webui-specific tests
pytest tests/unit/webui/ -v
pytest tests/integration/webui/ -v

# Run all tests with webui enabled
MCP_WRAPPER_WEB_UI=true pytest
```

## Screenshots

*Screenshots will be added after implementation*

## Related

- Follows P9-T2 (uvx documentation update)
- Part of Phase 10: Web UI Control & Audit Dashboard
