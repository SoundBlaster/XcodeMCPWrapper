# Web UI Dashboard

Real-time monitoring, metrics, and audit logging for MCP tool usage.

## Overview

The Web UI Dashboard is an optional component that provides live observability into the wrapper's
operation. Once enabled, open `http://localhost:8080` in a browser to view the dashboard.

## Installation

Install the Web UI extras alongside the wrapper:

```bash
pip install mcpbridge-wrapper[webui]
```

Or using the install script:

```bash
./scripts/install.sh --webui
```

## Enabling the Dashboard

Pass `--web-ui` when starting the wrapper. The dashboard is **only** active when this flag is
present — there is no runtime toggle.

```bash
# Default port 8080
xcodemcpwrapper --web-ui

# Custom port
xcodemcpwrapper --web-ui --web-ui-port 9090

# Custom config file
xcodemcpwrapper --web-ui --web-ui-config /path/to/webui.json
```

### Enabling via mcp.json

Add `--web-ui` and, optionally, `--web-ui-config` to the `args` array in your MCP client config:

```json
{
  "xcode-tools": {
    "command": "/Users/YOUR_USERNAME/bin/xcodemcpwrapper",
    "args": ["--web-ui", "--web-ui-port", "8080", "--web-ui-config", "/Users/YOUR_USERNAME/.config/xcodemcpwrapper/webui.json"],
    "env": {}
  }
}
```

## Configuration

Create a JSON file and pass its path with `--web-ui-config`. All fields are optional; unset fields
fall back to their defaults.

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
        "max_datapoints": 3600,
        "capture_params": false
    },
    "audit": {
        "enabled": true,
        "log_dir": "logs/audit",
        "max_file_size_mb": 10.0,
        "max_files": 10,
        "capture_payload": false
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
| `metrics.capture_params` | Record parameter key names per tool call for pattern analysis | `false` |
| `audit.enabled` | Enable audit logging | `true` |
| `audit.log_dir` | Audit log directory | `logs/audit` |
| `audit.max_file_size_mb` | Max log file size | `10.0` |
| `audit.max_files` | Max rotated log files | `10` |
| `audit.capture_payload` | Capture full request/response payloads in the ring buffer | `false` |
| `dashboard.refresh_interval_ms` | WebSocket update interval | `1000` |
| `dashboard.chart_history_seconds` | Chart history duration | `300` |

### Environment Variable Overrides

A subset of settings can be set via environment variables. Environment variables **only** cover
`host`, `port`, and `auth.*`. Options such as `metrics.capture_params` and `audit.capture_payload`
have no env var equivalent and must be set via `--web-ui-config`.

```bash
export WEBUI_HOST=0.0.0.0
export WEBUI_PORT=9000
export WEBUI_AUTH_ENABLED=true
export WEBUI_AUTH_USERNAME=myuser
export WEBUI_AUTH_PASSWORD=mypass
xcodemcpwrapper --web-ui
```

## Dashboard Features

### KPI Cards

- **Uptime** — How long the wrapper has been running
- **Total Requests** — Cumulative request count
- **Requests/sec** — Current throughput (60 s window)
- **Error Rate** — Percentage of failed requests
- **Total Errors** — Cumulative error count
- **In Flight** — Currently active requests

### Charts

- **Tool Usage (Bar)** — Call frequency per tool
- **Tool Distribution (Pie)** — Relative usage breakdown
- **Request Timeline** — Time-series of requests and errors
- **Latency** — Latency trends over time

### Per-Tool Latency Statistics

Table showing Avg / P50 / P95 / P99 / Min / Max latency per tool.

### Audit Log

Paginated table of recent tool calls with timestamp, tool name, direction, request ID, latency,
and error message. Supports filter by tool name, JSON export, and CSV export.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check (no auth required) |
| `/api/metrics` | GET | Current metrics summary |
| `/api/metrics/timeseries` | GET | Time-series data for charts |
| `/api/metrics/reset` | POST | Reset all metrics |
| `/api/audit` | GET | Query audit logs (with pagination) |
| `/api/audit/export/json` | GET | Export audit as JSON |
| `/api/audit/export/csv` | GET | Export audit as CSV |
| `/api/config` | GET | Current configuration (password masked) |
| `/ws/metrics` | WebSocket | Real-time metrics stream |

## Security

The dashboard binds to `127.0.0.1` (localhost only) by default. Only change the host to `0.0.0.0`
if you understand the security implications.

Enable basic authentication:

```bash
export WEBUI_AUTH_ENABLED=true
export WEBUI_AUTH_USERNAME=admin
export WEBUI_AUTH_PASSWORD=your-secure-password
```

## Troubleshooting

**Web UI dependencies missing:**
```
Error: Web UI dependencies not installed. Install with: pip install mcpbridge-wrapper[webui]
```
Run `pip install mcpbridge-wrapper[webui]` or `./scripts/install.sh --webui`.

**Port already in use:**
```bash
xcodemcpwrapper --web-ui --web-ui-port 9090
# or
export WEBUI_PORT=9090
```

**Dashboard shows Disconnected:** Refresh the page and check the browser console for WebSocket
errors. The dashboard falls back to HTTP polling if WebSocket fails.

**High memory usage:** Lower retention limits in the config:
```json
{
    "metrics": { "window_seconds": 1800, "max_datapoints": 1800 },
    "audit": { "max_file_size_mb": 5.0, "max_files": 5 }
}
```

## Performance

- Metrics collection adds < 1 % overhead
- WebSocket updates every 1 second
- Audit logging is asynchronous
- Memory-bounded data structures
