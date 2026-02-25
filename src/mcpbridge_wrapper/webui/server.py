"""FastAPI web server for the XcodeMCPWrapper dashboard.

Provides REST API endpoints for metrics and audit data, WebSocket
for real-time updates, static file serving for the dashboard frontend,
and optional basic authentication.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import secrets
import socket
import sys
import threading
from typing import TYPE_CHECKING, Any, Callable

from mcpbridge_wrapper.webui.audit import AuditLogger
from mcpbridge_wrapper.webui.config import WebUIConfig
from mcpbridge_wrapper.webui.metrics import MetricsCollector
from mcpbridge_wrapper.webui.sessions import detect_sessions

_IMPORT_ERROR: ImportError | None = None
uvicorn: Any | None = None

try:
    import uvicorn as _uvicorn
    from fastapi import FastAPI, HTTPException, Query, Request, WebSocket
    from fastapi.responses import HTMLResponse, PlainTextResponse, Response
    from fastapi.staticfiles import StaticFiles

    uvicorn = _uvicorn
except ImportError as e:
    if TYPE_CHECKING:  # pragma: no cover - type hints only
        from fastapi import FastAPI, HTTPException, Query, Request, WebSocket
        from fastapi.responses import HTMLResponse, PlainTextResponse, Response
        from fastapi.staticfiles import StaticFiles
    else:
        FastAPI = HTTPException = Query = Request = WebSocket = object  # type: ignore
        HTMLResponse = PlainTextResponse = Response = object  # type: ignore
        StaticFiles = object  # type: ignore

    _IMPORT_ERROR = e

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _entry_timestamp(entry: dict[str, Any]) -> float:
    """Return a sortable timestamp value for a session entry."""
    try:
        return float(entry.get("timestamp", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _sorted_session_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize audit entries to chronological order for session detection."""
    return sorted(entries, key=_entry_timestamp)


def is_port_available(host: str, port: int) -> bool:
    """Check whether *host:port* is available for binding.

    Returns ``True`` if the port can be bound (i.e. it is free), ``False``
    if the address is already in use or otherwise unavailable.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _require_webui_deps() -> None:
    """Ensure Web UI dependencies are available."""
    if _IMPORT_ERROR is not None:
        raise ImportError(
            "Web UI dependencies not installed. Install with: pip install mcpbridge-wrapper[webui]"
        ) from _IMPORT_ERROR


def _decode_basic_auth_value(value: str) -> tuple[str, str] | None:
    """Decode a Basic auth value into username/password."""
    if not value.startswith("Basic "):
        return None

    try:
        decoded = base64.b64decode(value[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return None

    return username, password


def _credentials_match(username: str, password: str, config: WebUIConfig) -> bool:
    """Check whether provided credentials match configured dashboard auth."""
    return bool(
        secrets.compare_digest(username, config.auth_username)
        and secrets.compare_digest(password, config.auth_password)
    )


def _check_auth(request: Request, config: WebUIConfig) -> None:
    """Validate Basic authentication if enabled.

    Args:
        request: The incoming HTTP request.
        config: Web UI configuration.

    Raises:
        HTTPException: If authentication fails.
    """
    if not config.auth_enabled:
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="XcodeMCPWrapper Dashboard"'},
        )

    credentials = _decode_basic_auth_value(auth_header)
    if credentials is None:
        raise HTTPException(status_code=401, detail="Invalid credentials") from None

    username, password = credentials
    if not _credentials_match(username, password, config):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="XcodeMCPWrapper Dashboard"'},
        )


def _check_websocket_auth(websocket: WebSocket, config: WebUIConfig) -> bool:
    """Validate websocket auth via Basic header or token query parameter."""
    if not config.auth_enabled:
        return True

    # Prefer standard Authorization header if provided.
    auth_header = websocket.headers.get("authorization", "")
    credentials = _decode_basic_auth_value(auth_header)
    if credentials is not None and _credentials_match(credentials[0], credentials[1], config):
        return True

    # Backward-compatible fallback: base64(username:password) via ?token=...
    token = websocket.query_params.get("token", "")
    if token:
        credentials = _decode_basic_auth_value(f"Basic {token}")
        if credentials is not None and _credentials_match(credentials[0], credentials[1], config):
            return True

    return False


def create_app(
    config: WebUIConfig,
    metrics: MetricsCollector,
    audit: AuditLogger,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Web UI configuration.
        metrics: Metrics collector instance.
        audit: Audit logger instance.

    Returns:
        Configured FastAPI application.
    """
    _require_webui_deps()
    app = FastAPI(
        title="XcodeMCPWrapper Dashboard",
        description="Real-time monitoring and control dashboard for XcodeMCPWrapper",
        version="1.0.0",
    )

    # Store references for access in routes
    app.state.config = config
    app.state.metrics = metrics
    app.state.audit = audit
    ws_clients: list[WebSocket] = []
    app.state.ws_clients = ws_clients

    # --- Authentication dependency ---

    async def require_auth(request: Request) -> None:
        """Dependency that enforces authentication."""
        _check_auth(request, config)

    # --- Dashboard routes ---

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> Response:
        """Serve the main dashboard page."""
        _check_auth(request, config)
        index_path = os.path.join(_STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            with open(index_path, encoding="utf-8") as f:
                html = f.read()

            ws_token = ""
            if config.auth_enabled:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Basic "):
                    ws_token = auth_header[6:]
            html = html.replace("__WS_AUTH_TOKEN_JSON__", json.dumps(ws_token))

            return HTMLResponse(content=html)
        return HTMLResponse("<h1>XcodeMCPWrapper Dashboard</h1><p>Static files not found.</p>")

    # --- Static files ---
    if os.path.isdir(_STATIC_DIR):
        app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    # --- API: Metrics ---

    @app.get("/api/metrics")
    async def get_metrics(request: Request) -> dict[str, Any]:
        """Get current metrics summary."""
        _check_auth(request, config)
        return metrics.get_summary()

    @app.get("/api/metrics/timeseries")
    async def get_timeseries(
        request: Request,
        seconds: int = Query(default=300, ge=10, le=86400),
    ) -> dict[str, Any]:
        """Get time-series metrics data for charting."""
        _check_auth(request, config)
        return metrics.get_timeseries(seconds)

    @app.post("/api/metrics/reset")
    async def reset_metrics(request: Request) -> dict[str, str]:
        """Reset all metrics counters."""
        _check_auth(request, config)
        metrics.reset()
        return {"status": "ok", "message": "Metrics reset"}

    # --- API: Audit ---

    @app.get("/api/audit")
    async def get_audit_logs(
        request: Request,
        limit: int = Query(default=100, ge=1, le=10000),
        offset: int = Query(default=0, ge=0),
        tool: str | None = Query(default=None),
    ) -> dict[str, Any]:
        """Get audit log entries."""
        _check_auth(request, config)
        entries = audit.get_entries(limit=limit, offset=offset, tool_filter=tool)
        return {
            "entries": entries,
            "total": audit.get_entry_count(),
            "limit": limit,
            "offset": offset,
        }

    @app.get("/api/audit/{request_id}/detail")
    async def get_audit_detail(request: Request, request_id: str) -> dict[str, Any]:
        """Get full request/response payload for a specific audit entry."""
        _check_auth(request, config)
        payload = audit.get_payload(request_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Payload not found")
        return {"request_id": request_id, **payload}

    @app.get("/api/audit/export/json")
    async def export_audit_json(
        request: Request,
        limit: int | None = Query(default=None, ge=1),
    ) -> Response:
        """Export audit logs as JSON file."""
        _check_auth(request, config)
        content = audit.export_json(limit=limit)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_log.json"},
        )

    @app.get("/api/audit/export/csv")
    async def export_audit_csv(
        request: Request,
        limit: int | None = Query(default=None, ge=1),
    ) -> Response:
        """Export audit logs as CSV file."""
        _check_auth(request, config)
        content = audit.export_csv(limit=limit)
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
        )

    # --- API: Sessions ---

    @app.get("/api/sessions")
    async def get_sessions(
        request: Request,
        gap_seconds: int = Query(default=None, ge=10, le=86400),
        limit: int = Query(default=10000, ge=1, le=10000),
    ) -> dict[str, Any]:
        """Get tool call sessions grouped by idle gap."""
        _check_auth(request, config)
        effective_gap = gap_seconds if gap_seconds is not None else config.session_gap_seconds
        entries = _sorted_session_entries(audit.get_entries(limit=limit))
        sessions = detect_sessions(entries, gap_seconds=float(effective_gap))
        return {"sessions": sessions, "total": len(sessions)}

    # --- API: Analytics ---

    @app.get("/api/analytics/param-patterns")
    async def get_param_patterns(
        request: Request,
        tool: str = Query(..., description="Tool name to query param patterns for"),
        top_n: int = Query(default=10, ge=1, le=100),
    ) -> dict[str, Any]:
        """Get the most common parameter key combinations for a tool."""
        _check_auth(request, config)
        patterns = metrics.get_param_patterns(tool, top_n=top_n)
        return {"tool": tool, "patterns": patterns}

    # --- API: Configuration ---

    @app.get("/api/config")
    async def get_config(request: Request) -> dict[str, Any]:
        """Get current configuration (passwords masked)."""
        _check_auth(request, config)
        return config.to_dict()

    # --- API: Health ---

    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint (no auth required)."""
        return {"status": "ok"}

    # --- WebSocket: Real-time metrics ---

    @app.websocket("/ws/metrics")
    async def ws_metrics(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time metrics streaming."""
        if not _check_websocket_auth(websocket, config):
            await websocket.close(code=4003, reason="Unauthorized")
            return

        await websocket.accept()
        app.state.ws_clients.append(websocket)

        try:
            while True:
                # Send metrics every refresh interval
                summary = metrics.get_summary()
                timeseries = metrics.get_timeseries(config.chart_history_seconds)
                entries = _sorted_session_entries(audit.get_entries(limit=10000))
                sessions = detect_sessions(entries, gap_seconds=float(config.session_gap_seconds))
                await websocket.send_json(
                    {
                        "type": "metrics_update",
                        "summary": summary,
                        "timeseries": timeseries,
                        "sessions": sessions,
                    }
                )
                await asyncio.sleep(config.dashboard_refresh_interval_ms / 1000.0)
        except Exception:
            pass
        finally:
            if websocket in app.state.ws_clients:
                app.state.ws_clients.remove(websocket)

    return app


def run_server(
    config: WebUIConfig,
    metrics: MetricsCollector,
    audit: AuditLogger,
    on_started: Callable[[], None] | None = None,
) -> None:
    """Start the web UI server (blocking).

    Args:
        config: Web UI configuration.
        metrics: Metrics collector instance.
        audit: Audit logger instance.
        on_started: Optional callback invoked after server starts.
    """
    _require_webui_deps()
    assert uvicorn is not None
    app = create_app(config, metrics, audit)

    server_config = uvicorn.Config(
        app,
        host=config.host,
        port=config.port,
        log_level="warning",
        access_log=False,
    )

    # Avoid monkey-patching uvicorn Server methods (mypy rejects method assignment).
    # Instead, trigger the callback just before starting the blocking server loop.
    if on_started:
        on_started()

    try:
        uvicorn.run(
            app,
            host=server_config.host,
            port=server_config.port,
            log_level=server_config.log_level,
            access_log=server_config.access_log,
        )
    except OSError as exc:
        print(
            f"Warning: Web UI server could not bind to "
            f"{server_config.host}:{server_config.port}: {exc}",
            file=sys.stderr,
        )
    except SystemExit:
        # uvicorn calls sys.exit(1) when port binding fails internally (e.g. TOCTOU window
        # where port became occupied after is_port_available() returned True). Catch here so
        # the daemon thread exits cleanly without an unhandled thread exception.
        print(
            f"Warning: Web UI server failed to start on "
            f"{server_config.host}:{server_config.port}. "
            "Port may have become occupied after the availability check. "
            "MCP bridge continues without the dashboard.",
            file=sys.stderr,
        )


def run_server_in_thread(
    config: WebUIConfig,
    metrics: MetricsCollector,
    audit: AuditLogger,
) -> threading.Thread:
    """Start the web UI server in a daemon thread.

    Args:
        config: Web UI configuration.
        metrics: Metrics collector instance.
        audit: Audit logger instance.

    Returns:
        The daemon thread running the server.
    """
    _require_webui_deps()
    thread = threading.Thread(
        target=run_server,
        args=(config, metrics, audit),
        daemon=True,
        name="webui-server",
    )
    thread.start()
    return thread
