# P10-T1: Web UI Control & Audit Dashboard

## Overview

Create a web-based dashboard for real-time monitoring, control, and audit logging of the XcodeMCPWrapper. This provides visibility into MCP tool usage, performance metrics, and operational control for developers and system administrators.

## Problem Statement

Currently, the XcodeMCPWrapper operates as a black-box stdio bridge. Users have no visibility into:
- Which MCP tools are being called and how frequently
- Request/response latency and performance metrics
- Error rates and failure patterns
- Active connections and concurrent operations
- Historical audit trail of tool invocations

## Solution

A lightweight web dashboard that exposes operational metrics and provides control capabilities through a clean, modern interface.

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

## Functional Requirements

### FR1: Real-time Metrics Dashboard
- Display current active connections
- Show requests per second (RPS) counter
- Display average response latency (p50, p95, p99)
- Show error rate percentage
- Live updating via WebSocket (no page refresh)

### FR2: Tool Usage Analytics
- Bar chart of most frequently called tools (top 10)
- Pie chart of tool categories (File Ops, Build, Test, Diagnostics, Advanced)
- Timeline graph of tool calls over time (last 1h, 24h, 7d)
- Success vs failure rate per tool

### FR3: Request/Response Inspector
- Live log stream of recent tool calls
- Search/filter by tool name, status (success/error), time range
- Expandable detail view showing full request/response JSON
- Export capability (JSON/CSV) for debugging

### FR4: Audit Logging
- Persistent log of all MCP interactions
- Log rotation (keep last 30 days by default, configurable)
- Structured logging with timestamps, tool names, arguments, results
- Compliance-ready audit trail (who/what/when)

### FR5: Control Interface
- Start/Stop/Restart wrapper service
- Configuration viewer (read-only for safety)
- Environment variable display (sanitized)
- Health check status indicator

### FR6: Alerting (Future Enhancement)
- Configurable thresholds for error rates
- Notification hooks (webhook, email)
- Alert history log

## Non-Functional Requirements

### NFR1: Performance
- Dashboard UI must not impact wrapper performance (< 1% overhead)
- WebSocket updates every 1 second maximum
- Page load time < 2 seconds

### NFR2: Security
- Optional authentication (basic auth or API key)
- Bind to localhost only by default (127.0.0.1)
- No sensitive data exposure (sanitize paths, tokens)

### NFR3: Resource Usage
- Web UI memory footprint < 20MB
- Log storage < 100MB default (configurable)

### NFR4: Compatibility
- Works with existing wrapper without modification
- Optional feature - wrapper works without Web UI
- Python 3.7+ compatible

## Implementation Plan

### Phase 10.1: Core Infrastructure
1. Create `src/mcpbridge_wrapper/webui/` package
2. Implement metrics collection hooks in wrapper core
3. Create in-memory metrics store with thread-safe operations
4. Add optional `--web-ui` CLI flag to enable dashboard

### Phase 10.2: Web Server
1. Implement FastAPI-based web server
2. Create REST API endpoints for metrics
3. Implement WebSocket for real-time updates
4. Add CORS and security middleware

### Phase 10.3: Frontend Dashboard
1. Create static HTML/CSS/JS dashboard
2. Implement Chart.js for visualizations
3. Build live log table with filtering
4. Add control buttons (start/stop/restart)

### Phase 10.4: Audit Logging
1. Implement structured JSON logger
2. Add log rotation mechanism
3. Create log viewer in dashboard
4. Add export functionality

### Phase 10.5: Testing & Documentation
1. Unit tests for metrics collection
2. Integration tests for WebSocket
3. Update documentation with Web UI setup
4. Add troubleshooting guide

## File Structure

```
src/mcpbridge_wrapper/
├── webui/
│   ├── __init__.py
│   ├── server.py          # FastAPI server
│   ├── metrics.py         # Metrics collection
│   ├── audit.py           # Audit logging
│   ├── config.py          # Web UI configuration
│   └── static/
│       ├── index.html     # Dashboard UI
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           ├── dashboard.js
│           └── charts.js
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve dashboard HTML |
| `/api/health` | GET | Health check status |
| `/api/metrics` | GET | Current metrics snapshot |
| `/api/metrics/history` | GET | Historical metrics (1h, 24h, 7d) |
| `/api/tools` | GET | Tool usage statistics |
| `/api/logs` | GET | Recent audit logs (paginated) |
| `/api/logs/export` | GET | Export logs (JSON/CSV) |
| `/api/control/status` | GET | Wrapper service status |
| `/api/control/{action}` | POST | Control actions (start/stop/restart) |
| `/ws` | WebSocket | Real-time metrics stream |

## Configuration

```python
# config/webui.json
{
  "enabled": false,
  "host": "127.0.0.1",
  "port": 8080,
  "auth": {
    "enabled": false,
    "type": "basic",
    "username": "admin",
    "password_hash": "..."
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

## Usage

### Enable Web UI

```bash
# Via command line
xcodemcpwrapper --web-ui --web-ui-port 8080

# Via environment variable
export MCP_WRAPPER_WEB_UI=true
export MCP_WRAPPER_WEB_UI_PORT=8080
xcodemcpwrapper
```

### Access Dashboard

Open browser to `http://localhost:8080`

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

```
# Optional dependencies (only when webui is enabled)
fastapi>=0.100.0
uvicorn>=0.23.0
websockets>=11.0
python-multipart>=0.0.6

# Frontend (bundled, no external CDN)
Chart.js 4.x (MIT License)
```

## Future Enhancements

- Authentication with OAuth/GitHub
- Remote access with secure tunnel
- Custom dashboard widgets
- Alerting and notifications
- Multi-wrapper aggregation
- Performance profiling per tool

---
**Archived:** 2026-02-09
**Verdict:** PASS
