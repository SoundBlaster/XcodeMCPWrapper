"""Terminal frontend for broker daemon monitoring and control."""

from __future__ import annotations

import base64
import contextlib
import ipaddress
import json
import os
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcpbridge_wrapper.broker.types import BrokerConfig
from mcpbridge_wrapper.webui.config import WebUIConfig


@dataclass
class TUIRuntimeConfig:
    """Resolved runtime settings for the broker terminal UI."""

    base_url: str
    auth_header: str | None
    log_path: Path
    pid_file: Path = field(default_factory=lambda: BrokerConfig.default().pid_file)
    socket_path: Path = field(default_factory=lambda: BrokerConfig.default().socket_path)
    version_file: Path = field(default_factory=lambda: BrokerConfig.default().version_file)
    timeout_seconds: float = 1.5
    refresh_interval_seconds: float = 1.0
    recent_log_lines: int = 8


@dataclass
class BrokerTUISnapshot:
    """Operator-facing snapshot rendered by the broker terminal UI."""

    base_url: str
    service_name: str
    can_stop: bool
    available: bool
    broker: dict[str, Any] | None
    recent_events: list[str]
    local_pid: int | None = None
    local_daemon_running: bool = False
    local_socket_present: bool = False
    local_daemon_version: str | None = None
    local_pid_file: str = "n/a"
    local_socket_path: str = "n/a"
    local_version_file: str = "n/a"
    runtime_source: str = "dashboard-api"
    error_message: str | None = None
    status_message: str | None = None
    refreshed_at: float = field(default_factory=time.time)


def build_tui_runtime(
    *,
    web_ui_port: int | None,
    web_ui_config: str | None,
) -> TUIRuntimeConfig:
    """Resolve endpoint, auth, and log-path settings for TUI mode."""
    config = WebUIConfig(config_path=web_ui_config)
    if web_ui_port is not None:
        config._data["port"] = web_ui_port

    auth_header: str | None = None
    if config.auth_enabled:
        raw_credentials = f"{config.auth_username}:{config.auth_password}".encode()
        token = base64.b64encode(raw_credentials).decode("ascii")
        auth_header = f"Basic {token}"

    client_host = _client_host_for_base_url(config.host)
    broker_state_dir = BrokerConfig.default().pid_file.parent
    return TUIRuntimeConfig(
        base_url=f"http://{client_host}:{config.port}",
        auth_header=auth_header,
        log_path=broker_state_dir / "broker.log",
        pid_file=broker_state_dir / "broker.pid",
        socket_path=broker_state_dir / "broker.sock",
        version_file=broker_state_dir / "broker.version",
    )


def tail_log_lines(log_path: Path, max_lines: int = 8) -> list[str]:
    """Return the last ``max_lines`` from the broker log with friendly fallbacks."""
    if max_lines <= 0:
        return []

    if not log_path.exists():
        return [f"(no broker log at {log_path})"]

    try:
        chunks: list[bytes] = []
        newline_count = 0
        with log_path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()

            while position > 0 and newline_count <= max_lines:
                read_size = min(4096, position)
                position -= read_size
                handle.seek(position)
                chunk = handle.read(read_size)
                chunks.append(chunk)
                newline_count += chunk.count(b"\n")

        text = b"".join(reversed(chunks)).decode("utf-8", errors="replace")
    except OSError as exc:
        return [f"(cannot read broker log at {log_path}: {exc})"]

    lines = text.splitlines()
    if not lines:
        return ["(broker log is empty)"]

    return lines[-max_lines:]


class BrokerTUIClient:
    """HTTP-backed client used by the terminal frontend."""

    def __init__(self, runtime: TUIRuntimeConfig) -> None:
        """Store runtime settings for later polling and control calls."""
        self._runtime = runtime

    def fetch_snapshot(self, status_message: str | None = None) -> BrokerTUISnapshot:
        """Fetch control + broker status and merge them into one render snapshot."""
        recent_events = tail_log_lines(
            self._runtime.log_path,
            max_lines=self._runtime.recent_log_lines,
        )
        local_pid, local_running = _read_local_pid(self._runtime.pid_file)
        local_version = _read_local_version(self._runtime.version_file)
        local_socket_present = self._runtime.socket_path.exists()
        local_fallback_broker = _build_local_fallback_broker(
            runtime=self._runtime,
            local_pid=local_pid,
            local_running=local_running,
            local_socket_present=local_socket_present,
            local_version=local_version,
        )

        try:
            control, broker_status = self.probe_backend()
        except RuntimeError as exc:
            return BrokerTUISnapshot(
                base_url=self._runtime.base_url,
                service_name="local-fallback" if local_fallback_broker else "unavailable",
                can_stop=False,
                available=False,
                broker=local_fallback_broker,
                recent_events=recent_events,
                local_pid=local_pid,
                local_daemon_running=local_running,
                local_socket_present=local_socket_present,
                local_daemon_version=local_version,
                local_pid_file=str(self._runtime.pid_file),
                local_socket_path=str(self._runtime.socket_path),
                local_version_file=str(self._runtime.version_file),
                runtime_source=(
                    "local-fallback" if local_fallback_broker else "dashboard-unavailable"
                ),
                error_message=str(exc),
                status_message=status_message,
            )

        service_name = str(
            broker_status.get("service_name") or control.get("service_name") or "mcpbridge-wrapper"
        )
        broker_payload = broker_status.get("broker")
        broker = broker_payload if isinstance(broker_payload, dict) else None
        status_error = broker_status.get("error")

        return BrokerTUISnapshot(
            base_url=self._runtime.base_url,
            service_name=service_name,
            can_stop=bool(control.get("can_stop")),
            available=bool(broker_status.get("available")),
            broker=broker,
            recent_events=recent_events,
            local_pid=local_pid,
            local_daemon_running=local_running,
            local_socket_present=local_socket_present,
            local_daemon_version=local_version,
            local_pid_file=str(self._runtime.pid_file),
            local_socket_path=str(self._runtime.socket_path),
            local_version_file=str(self._runtime.version_file),
            runtime_source="dashboard-api",
            error_message=status_error if isinstance(status_error, str) and status_error else None,
            status_message=status_message,
        )

    def probe_backend(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Return raw control and broker-status payloads from the dashboard API."""
        control = self._request_json("/api/control")
        broker_status = self._request_json("/api/broker/status")
        return control, broker_status

    def request_stop(self) -> tuple[bool, str]:
        """Request broker shutdown through the control API."""
        try:
            payload = self._request_json("/api/control/stop", method="POST")
        except RuntimeError as exc:
            return False, str(exc)

        message = payload.get("message")
        if not isinstance(message, str) or not message:
            message = "Shutdown requested."
        return True, message

    def _request_json(self, path: str, method: str = "GET") -> dict[str, Any]:
        """Perform a JSON request against the local Web UI API."""
        url = f"{self._runtime.base_url.rstrip('/')}{path}"
        request = urllib.request.Request(url, method=method)
        request.add_header("Accept", "application/json")
        if self._runtime.auth_header:
            request.add_header("Authorization", self._runtime.auth_header)

        try:
            with urllib.request.urlopen(request, timeout=self._runtime.timeout_seconds) as response:
                payload = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            detail = _extract_http_error(payload) or str(exc.reason or exc)
            raise RuntimeError(f"{method} {path} failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason if exc.reason is not None else exc
            raise RuntimeError(f"Cannot reach {self._runtime.base_url}: {reason}") from exc

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{method} {path} returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise RuntimeError(f"{method} {path} returned an unexpected payload.")

        return data


def render_screen(snapshot: BrokerTUISnapshot, width: int) -> list[str]:
    """Build wrapped screen lines for the current broker snapshot."""
    broker = snapshot.broker or {}
    lines = [
        "mcpbridge-wrapper Broker TUI",
        "Keys: q quit | r refresh | s stop broker",
        "",
        f"Endpoint: {snapshot.base_url}",
        f"Service: {snapshot.service_name}",
        f"Stop Control: {_availability(snapshot.can_stop)}",
        "",
        "Local Broker Files",
        f"Local PID: {_display_value(snapshot.local_pid)}"
        + (" (running)" if snapshot.local_daemon_running else " (not running)"),
        f"Local Version: {_display_value(snapshot.local_daemon_version)}",
        f"Local Socket Present: {_yes_no(snapshot.local_socket_present)}",
        f"PID File: {_display_value(snapshot.local_pid_file)}",
        f"Socket Path: {_display_value(snapshot.local_socket_path)}",
        f"Version File: {_display_value(snapshot.local_version_file)}",
        "",
        "Broker Runtime",
        f"Runtime Source: {_runtime_source_label(snapshot.runtime_source)}",
    ]

    if broker:
        if snapshot.runtime_source == "local-fallback":
            lines.append("Dashboard API unavailable; showing local broker state only.")
        lines.extend(
            [
                f"State: {_display_value(broker.get('state'))}",
                f"Daemon PID: {_display_value(broker.get('pid'))}",
                f"Upstream PID: {_display_value(broker.get('upstream_pid'))}",
                f"Connected Clients: {_display_value(broker.get('connected_clients'))}",
                f"Upstream Alive: {_yes_no(broker.get('upstream_alive'))}",
                f"Initialized: {_yes_no(broker.get('upstream_initialized'))}",
                f"Tools Cached: {_yes_no(broker.get('tools_list_cached'))}",
                f"Reconnect Attempt: {_display_value(broker.get('reconnect_attempt'))}",
                f"Shutdown Requested: {_yes_no(broker.get('shutdown_requested'))}",
                f"Socket: {_display_value(broker.get('socket_path'))}",
            ]
        )
        if snapshot.runtime_source == "local-fallback":
            lines.append("Live control API is unavailable in local fallback mode.")
    else:
        lines.append("Broker runtime is unavailable.")
        if snapshot.error_message:
            lines.append(f"Error: {snapshot.error_message}")

    lines.extend(["", "Recent Broker Events"])
    lines.extend(snapshot.recent_events or ["(no broker events found)"])

    if snapshot.error_message and broker:
        lines.extend(["", f"Warning: {snapshot.error_message}"])

    lines.extend(
        [
            "",
            "Last Refresh: "
            + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(snapshot.refreshed_at)),
        ]
    )
    if snapshot.status_message:
        lines.append(f"Message: {snapshot.status_message}")

    return _wrap_lines(lines, width=max(20, width))


class BrokerTUI:
    """Thin curses shell around the broker TUI client and render helpers."""

    def __init__(self, client: BrokerTUIClient, refresh_interval_seconds: float = 1.0) -> None:
        """Store the polling client and refresh interval."""
        self._client = client
        self._refresh_interval_seconds = refresh_interval_seconds
        self._status_message: str | None = None

    def run(self) -> int:
        """Start the interactive terminal session."""
        import curses

        return int(curses.wrapper(self._run_loop))

    def _run_loop(self, stdscr: Any) -> int:
        """Drive the refresh and key-handling loop."""
        import curses

        with contextlib.suppress(Exception):
            curses.curs_set(0)

        stdscr.nodelay(True)
        stdscr.timeout(100)

        snapshot = self._client.fetch_snapshot(self._status_message)
        last_refresh = time.monotonic()

        while True:
            self._render(stdscr, snapshot)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return 0
            if key in (ord("r"), ord("R")):
                snapshot = self._client.fetch_snapshot(self._status_message)
                last_refresh = time.monotonic()
                continue
            if key in (ord("s"), ord("S")):
                if snapshot.can_stop:
                    _, self._status_message = self._client.request_stop()
                elif snapshot.runtime_source == "local-fallback":
                    self._status_message = (
                        "Stop control is unavailable without a live dashboard connection."
                    )
                else:
                    self._status_message = "Stop control is unavailable."
                snapshot = self._client.fetch_snapshot(self._status_message)
                last_refresh = time.monotonic()
                continue

            if time.monotonic() - last_refresh >= self._refresh_interval_seconds:
                snapshot = self._client.fetch_snapshot(self._status_message)
                last_refresh = time.monotonic()

    def _render(self, stdscr: Any, snapshot: BrokerTUISnapshot) -> None:
        """Render the current snapshot into the terminal window."""
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        lines = render_screen(snapshot, width=max(20, width - 1))

        # Keep the curses layer thin: rendering is pure and tested separately.
        for row, line in enumerate(lines[: max(1, height - 1)]):
            with contextlib.suppress(Exception):
                stdscr.addnstr(row, 0, line, max(1, width - 1))

        stdscr.refresh()


def run_tui(runtime: TUIRuntimeConfig) -> int:
    """Run the broker terminal frontend for the resolved runtime."""
    client = BrokerTUIClient(runtime)
    ui = BrokerTUI(client, refresh_interval_seconds=runtime.refresh_interval_seconds)
    return ui.run()


def _extract_http_error(payload: str) -> str | None:
    """Extract a human-readable detail string from an error payload."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return payload.strip() or None

    if not isinstance(data, dict):
        return payload.strip() or None

    detail = data.get("detail")
    if isinstance(detail, str) and detail:
        return detail

    message = data.get("message")
    if isinstance(message, str) and message:
        return message

    error = data.get("error")
    if isinstance(error, str) and error:
        return error

    return payload.strip() or None


def _client_host_for_base_url(host: str) -> str:
    """Convert a bind host into a client-friendly URL host component."""
    normalized_host = host.strip()
    if not normalized_host:
        return "127.0.0.1"

    with contextlib.suppress(ValueError):
        parsed_host = ipaddress.ip_address(normalized_host)
        if parsed_host.is_unspecified:
            return "[::1]" if parsed_host.version == 6 else "127.0.0.1"
        if parsed_host.version == 6:
            return f"[{normalized_host}]"
        return normalized_host

    return normalized_host


def _wrap_lines(lines: list[str], width: int) -> list[str]:
    """Wrap screen lines to fit the available width."""
    wrapped: list[str] = []
    effective_width = max(1, width)
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(
            textwrap.wrap(
                line,
                width=effective_width,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            or [""]
        )
    return wrapped


def _availability(value: bool) -> str:
    """Format availability for operator output."""
    return "available" if value else "unavailable"


def _yes_no(value: Any) -> str:
    """Format booleans for operator output."""
    return "yes" if bool(value) else "no"


def _display_value(value: Any) -> str:
    """Format possibly-missing values for operator output."""
    if value is None or value == "":
        return "n/a"
    return str(value)


def _runtime_source_label(source: str) -> str:
    """Render a stable runtime-source label for the TUI."""
    if source == "local-fallback":
        return "local broker files only"
    if source == "dashboard-unavailable":
        return "no reachable dashboard data"
    return "live dashboard API"


def _build_local_fallback_broker(
    *,
    runtime: TUIRuntimeConfig,
    local_pid: int | None,
    local_running: bool,
    local_socket_present: bool,
    local_version: str | None,
) -> dict[str, Any] | None:
    """Build a bounded local-only broker view when the dashboard is unavailable."""
    if local_running:
        return {
            "state": "running (local fallback)",
            "pid": local_pid,
            "socket_path": str(runtime.socket_path) if local_socket_present else None,
            "version": local_version,
        }

    if local_pid is not None or local_socket_present or local_version is not None:
        return {
            "state": "stale local state",
            "pid": local_pid,
            "socket_path": str(runtime.socket_path) if local_socket_present else None,
            "version": local_version,
        }

    return None


def _read_local_pid(pid_file: Path) -> tuple[int | None, bool]:
    """Read broker PID from file and report whether it is still alive."""
    if not pid_file.exists():
        return None, False

    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None, False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return pid, False
    except PermissionError:
        return pid, True
    return pid, True


def _read_local_version(version_file: Path) -> str | None:
    """Read broker version file if present."""
    if not version_file.exists():
        return None
    try:
        return version_file.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None
