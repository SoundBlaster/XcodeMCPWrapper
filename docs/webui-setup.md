# Web UI Dashboard Setup Guide

The XcodeMCPWrapper Web UI Dashboard provides real-time monitoring, metrics visualization, and audit logging for your MCP tool usage.

## Features

- **Real-time Metrics Dashboard**: Live RPS counter, latency percentiles (p50, p95, p99), error rates
- **Tool Usage Analytics**: Visual charts showing most frequently used tools
- **Request Timeline**: Time-series visualization of requests and errors
- **Per-Tool Latency Statistics**: Detailed latency breakdown by tool
- **Audit Logging**: Persistent log of all MCP tool calls with export capabilities
- **Optional Authentication**: Basic auth support for secure access

## Installation

### Install Web UI Dependencies

```bash
pip install mcpbridge-wrapper[webui]
```

Or install the extras manually:

```bash
pip install fastapi uvicorn websockets python-multipart
```

## Usage

### Enable Web UI via Command Line

```bash
# Start with Web UI on default port 8080
xcodemcpwrapper --web-ui

# Start with custom port
xcodemcpwrapper --web-ui --web-ui-port 9090

# Start with custom config file
xcodemcpwrapper --web-ui --web-ui-config /path/to/config.json
```

### Using Make Commands

```bash
# Install with Web UI dependencies
make install-webui

# Start Web UI dashboard
make webui

# Check Web UI health and metrics
make webui-health

# Run Web UI tests
make test-webui
```

### Enable Web UI via Environment Variables

```bash
export MCP_WRAPPER_WEB_UI=true
export MCP_WRAPPER_WEB_UI_PORT=8080
xcodemcpwrapper
```

### Access the Dashboard

Once started, open your browser to:

```
http://localhost:8080
```

## Configuration

Create a `webui.json` configuration file:

```json
{
    "host": "127.0.0.1",
    "port": 8080,
    "auth": {
        "enabled": false,
        "username": "admin",
        "password": "changeme"
    },
    "metrics": {
        "window_seconds": 3600,
        "max_datapoints": 3600
    },
    "audit": {
        "enabled": true,
        "log_dir": "logs/audit",
        "max_file_size_mb": 10.0,
        "max_files": 10
    },
    "dashboard": {
        "refresh_interval_ms": 1000,
        "chart_history_seconds": 300
    }
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `host` | Server bind address | `127.0.0.1` |
| `port` | Server port | `8080` |
| `auth.enabled` | Enable basic authentication | `false` |
| `auth.username` | Auth username | `admin` |
| `auth.password` | Auth password | `changeme` |
| `metrics.window_seconds` | Metrics rolling window | `3600` |
| `metrics.max_datapoints` | Max data points per series | `3600` |
| `audit.enabled` | Enable audit logging | `true` |
| `audit.log_dir` | Audit log directory | `logs/audit` |
| `audit.max_file_size_mb` | Max log file size | `10.0` |
| `audit.max_files` | Max rotated log files | `10` |
| `dashboard.refresh_interval_ms` | WebSocket update interval | `1000` |
| `dashboard.chart_history_seconds` | Chart history duration | `300` |

### Environment Variable Overrides

You can override config values via environment variables:

```bash
export WEBUI_HOST=0.0.0.0
export WEBUI_PORT=9000
export WEBUI_AUTH_ENABLED=true
export WEBUI_AUTH_USERNAME=myuser
export WEBUI_AUTH_PASSWORD=mypass
```

## Dashboard Overview

### KPI Cards

The top section displays key metrics:
- **Uptime**: How long the wrapper has been running
- **Total Requests**: Cumulative request count
- **Requests/sec**: Current throughput (60s window)
- **Error Rate**: Percentage of failed requests
- **Total Errors**: Cumulative error count
- **In Flight**: Currently active requests

### Charts

- **Tool Usage (Bar)**: Bar chart of tool call frequency
- **Tool Distribution (Pie)**: Pie chart showing tool usage breakdown
- **Request Timeline**: Time-series of requests and errors
- **Latency**: Latency trends over time

### Per-Tool Latency Statistics

A table showing detailed latency metrics per tool:
- Calls: Total number of calls
- Avg/P50/P95/P99: Latency percentiles
- Min/Max: Latency range

### Audit Log

A paginated table of recent tool calls with:
- Timestamp (ISO format)
- Tool name
- Direction (request/response)
- Request ID
- Latency (ms)
- Error message (if any)

Features:
- **Filter by tool name**: Type in the filter box
- **Pagination**: Navigate through history
- **Export JSON**: Download full audit log as JSON
- **Export CSV**: Download as CSV for spreadsheet analysis

## API Endpoints

The Web UI exposes a REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check (no auth) |
| `/api/metrics` | GET | Current metrics summary |
| `/api/metrics/timeseries` | GET | Time-series data for charts |
| `/api/metrics/reset` | POST | Reset all metrics |
| `/api/audit` | GET | Query audit logs (with pagination) |
| `/api/audit/export/json` | GET | Export audit as JSON |
| `/api/audit/export/csv` | GET | Export audit as CSV |
| `/api/config` | GET | Current configuration (masked) |
| `/ws/metrics` | WebSocket | Real-time metrics stream |

## Security

### Authentication

Enable basic authentication by setting `auth.enabled: true` in config or using the environment variable:

```bash
export WEBUI_AUTH_ENABLED=true
export WEBUI_AUTH_USERNAME=admin
export WEBUI_AUTH_PASSWORD=your-secure-password
```

**Note**: The dashboard binds to `127.0.0.1` (localhost only) by default for security. Only change to `0.0.0.0` if you understand the security implications.

### Audit Log Security

Audit logs contain MCP tool call data. Ensure:
- Log directory has appropriate permissions
- Log files are rotated to prevent disk exhaustion
- Sensitive data in requests/responses is sanitized before logging

## Troubleshooting

### Web UI Doesn't Start

```
Error: Web UI dependencies not installed. Install with: pip install mcpbridge-wrapper[webui]
```

Install the webui extras:
```bash
pip install mcpbridge-wrapper[webui]
```

### Port Already in Use

```
Address already in use
```

Change the port:
```bash
xcodemcpwrapper --web-ui --web-ui-port 9090
```

Or set via environment:
```bash
export WEBUI_PORT=9090
```

### Dashboard Shows Disconnected

- Check that the wrapper is still running
- Refresh the page
- Check browser console for WebSocket errors
- The dashboard falls back to HTTP polling if WebSocket fails

### High Memory Usage

Adjust retention settings in config:
```json
{
    "metrics": {
        "window_seconds": 1800,
        "max_datapoints": 1800
    },
    "audit": {
        "max_file_size_mb": 5.0,
        "max_files": 5
    }
}
```

## Performance

The Web UI is designed for minimal impact on wrapper performance:

- Metrics collection adds < 1% overhead
- WebSocket updates every 1 second
- Audit logging is asynchronous
- Memory-bounded data structures
- All heavy operations run in separate threads

## Uninstallation

To remove Web UI support:

```bash
pip uninstall fastapi uvicorn websockets python-multipart
```

Or reinstall without extras:

```bash
pip install mcpbridge-wrapper --force-reinstall
```
