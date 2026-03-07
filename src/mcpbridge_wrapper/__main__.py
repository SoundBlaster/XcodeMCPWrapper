"""Entry point for mcpbridge-wrapper."""

import contextlib
import os
import signal
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional, Set, Tuple

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    run_stdin_forwarder,
    run_stdout_reader,
    terminate_bridge_process,
)
from mcpbridge_wrapper.transform import process_response_line

# Diagnostic tracking
_seen_initialize = False
_seen_tools_request = False
_tools_response_timeout = False

# Guard rail for method-correlation tracking (FU-BUG-T7-1).
MAX_PENDING_METHODS = 1000

# After stdin EOF, allow a short window for in-flight responses before forcing
# upstream termination. This reduces dropped final responses in one-shot usage.
STDIN_EOF_DRAIN_TIMEOUT_SECONDS = 0.25
STDIN_EOF_DRAIN_POLL_INTERVAL_SECONDS = 0.01


def check_xcode_tools_enabled() -> None:
    """Print diagnostic message if Xcode Tools MCP is likely not enabled."""
    print(
        "\n⚠️  DIAGNOSTIC: Xcode Tools MCP service is not responding.\n"
        "   This usually means Xcode Tools MCP is not enabled in Xcode settings.\n\n"
        "   To fix this:\n"
        "   1. Open Xcode > Settings (⌘,)\n"
        "   2. Select 'Intelligence' in the sidebar\n"
        "   3. Under 'Model Context Protocol', toggle 'Xcode Tools' ON\n\n"
        "   Then restart Cursor/Zed/Claude and try again.\n",
        file=sys.stderr,
    )


def _parse_webui_port(raw_value: str) -> int:
    """Parse and validate web UI port value."""
    try:
        port = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid --web-ui-port value '{raw_value}'. Expected integer between 1 and 65535."
        ) from exc

    if port < 1 or port > 65535:
        raise ValueError(
            f"Invalid --web-ui-port value '{raw_value}'. Expected integer between 1 and 65535."
        )

    return port


def _parse_webui_args(
    args: list,
) -> Tuple[bool, bool, bool, Optional[int], Optional[str], list]:
    """Parse web UI arguments from command-line args.

    Extracts --web-ui, --web-ui-only, --web-ui-port, and --web-ui-config flags and
    returns them along with the remaining args to forward to the bridge.

    Args:
        args: Command-line arguments list.

    Returns:
        Tuple of (
            web_ui_enabled,
            web_ui_only_mode,
            web_ui_restart_mode,
            port_or_none,
            config_path_or_none,
            remaining_args,
        ).

    Raises:
        ValueError: If --web-ui-port is not an integer in [1, 65535].
    """
    web_ui = False
    web_ui_only = False
    web_ui_restart = False
    port: Optional[int] = None
    config_path: Optional[str] = None
    remaining = []

    i = 0
    while i < len(args):
        if args[i] == "--web-ui":
            web_ui = True
            i += 1
        elif args[i] == "--web-ui-only":
            # Standalone dashboard mode (no bridge process). Implicitly enables Web UI.
            web_ui = True
            web_ui_only = True
            i += 1
        elif args[i] == "--web-ui-restart":
            # Restart mode is meaningful only when Web UI is enabled.
            web_ui = True
            web_ui_restart = True
            i += 1
        elif args[i] == "--web-ui-port" and i + 1 < len(args):
            port = _parse_webui_port(args[i + 1])
            i += 2
        elif args[i].startswith("--web-ui-port="):
            port = _parse_webui_port(args[i].split("=", 1)[1])
            i += 1
        elif args[i] == "--web-ui-config" and i + 1 < len(args):
            config_path = args[i + 1]
            i += 2
        elif args[i].startswith("--web-ui-config="):
            config_path = args[i].split("=", 1)[1]
            i += 1
        else:
            remaining.append(args[i])
            i += 1

    return web_ui, web_ui_only, web_ui_restart, port, config_path, remaining


def _parse_tui_args(args: list) -> Tuple[bool, list]:
    """Parse terminal frontend arguments from command-line args."""
    tui_enabled = False
    remaining = []

    for arg in args:
        if arg == "--tui":
            tui_enabled = True
        else:
            remaining.append(arg)

    return tui_enabled, remaining


def _parse_broker_console_args(args: list) -> Tuple[bool, list]:
    """Parse one-command broker console arguments from command-line args."""
    broker_console = False
    remaining = []

    for arg in args:
        if arg == "--broker-console":
            broker_console = True
        else:
            remaining.append(arg)

    return broker_console, remaining


def _parse_doctor_args(args: list) -> Tuple[bool, list]:
    """Parse diagnostics mode arguments from command-line args."""
    doctor_enabled = False
    remaining = []

    for arg in args:
        if arg == "--doctor":
            doctor_enabled = True
        else:
            remaining.append(arg)

    return doctor_enabled, remaining


def _find_listener_pids_for_port(port: int) -> Set[int]:
    """Return listener PIDs bound to TCP port, or empty set when none found."""
    try:
        result = subprocess.run(
            ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return set()

    pids: Set[int] = set()
    for raw in result.stdout.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        with contextlib.suppress(ValueError):
            pids.add(int(raw))
    return pids


def _pid_exists(pid: int) -> bool:
    """Return True when process exists and caller has permission to probe it."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_pids_gracefully_then_force(
    pids: Set[int],
    grace_timeout_seconds: float = 1.5,
    poll_interval_seconds: float = 0.05,
) -> bool:
    """Terminate PIDs with SIGTERM, then SIGKILL remaining after timeout."""
    if not pids:
        return True

    for pid in pids:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(pid, signal.SIGTERM)

    deadline = time.monotonic() + grace_timeout_seconds
    remaining = set(pids)
    while remaining and time.monotonic() < deadline:
        remaining = {pid for pid in remaining if _pid_exists(pid)}
        if not remaining:
            return True
        time.sleep(poll_interval_seconds)

    for pid in remaining:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(pid, signal.SIGKILL)

    remaining = {pid for pid in remaining if _pid_exists(pid)}
    return not remaining


def _restart_webui_listener(host: str, port: int) -> bool:
    """Try to free Web UI port by terminating stale listeners."""
    del host  # Reserved for future host-specific diagnostics.

    stale_pids = _find_listener_pids_for_port(port)
    if not stale_pids:
        return True
    return _terminate_pids_gracefully_then_force(stale_pids)


def _extract_tool_name(line: str) -> Optional[str]:
    """Extract the MCP tool name from a JSON-RPC request/response line.

    Uses schema validation to correctly parse MCP protocol format.

    Args:
        line: A line from the bridge output.

    Returns:
        The tool name if found, None otherwise.
    """
    try:
        from mcpbridge_wrapper.schemas import MCPRequest, MCPResponse

        # Try parsing as request first
        req = MCPRequest.model_validate_json(line)
        tool_name = req.get_tool_name()
        if tool_name:
            return tool_name

        # Try parsing as response
        resp = MCPResponse.model_validate_json(line)
        return resp.get_tool_name()
    except Exception:
        return None


def _extract_request_id(line: str) -> Optional[str]:
    """Extract the JSON-RPC request ID from a line.

    Args:
        line: A line from the bridge output.

    Returns:
        The request ID as a string if found, None otherwise.
    """
    try:
        from mcpbridge_wrapper.schemas import MCPRequest

        req = MCPRequest.model_validate_json(line)
        if req.id is not None:
            return str(req.id)
    except Exception:
        pass
    return None


def _parse_error_info(line: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Parse error status, code, and message from a JSON-RPC response line.

    Args:
        line: A line from the bridge output.

    Returns:
        Tuple of (is_error, error_code, error_message).
    """
    try:
        from mcpbridge_wrapper.schemas import MCPResponse

        resp = MCPResponse.model_validate_json(line)
        return resp.has_error(), resp.get_error_code(), resp.get_error_message()
    except Exception:
        return False, None, None


def _has_error(line: str) -> bool:
    """Check if a JSON-RPC response contains an error.

    Args:
        line: A line from the bridge output.

    Returns:
        True if the line contains an error response.
    """
    is_error, _, _ = _parse_error_info(line)
    return is_error


def _parse_broker_args(
    args: list,
) -> Tuple[bool, bool, bool, bool, bool, list]:
    """Parse broker arguments from command-line args.

    Extracts ``--broker-daemon``, ``--broker``, ``--broker-status``, and
    ``--broker-stop`` flags and returns them along with the remaining args
    to forward to the bridge.  Broker-only flags are *never* forwarded to
    ``xcrun mcpbridge``.

    ``--broker`` is the recommended flag: it auto-detects whether a daemon is
    already running and spawns one if needed.

    Args:
        args: Command-line arguments list.

    Returns:
        Tuple of (broker_daemon, broker_connect, broker_spawn,
                  broker_status, broker_stop, remaining_args).
    """
    broker_daemon = False
    broker_connect = False
    broker_spawn = False
    broker_status = False
    broker_stop = False
    remaining = []

    for arg in args:
        if arg == "--broker-daemon":
            broker_daemon = True
        elif arg == "--broker":
            # Recommended flag: auto-detect (spawn if needed, then connect).
            broker_spawn = True
            broker_connect = True
        elif arg == "--broker-status":
            broker_status = True
        elif arg == "--broker-stop":
            broker_stop = True
        else:
            remaining.append(arg)

    return broker_daemon, broker_connect, broker_spawn, broker_status, broker_stop, remaining


def _track_pending_method(
    pending_methods: Dict[str, str],
    request_id: str,
    method: str,
    max_size: int,
) -> None:
    """Track request method with bounded map size.

    Uses insertion order for eviction: when at capacity, drop the oldest pending
    request before adding a new one. Re-seen request IDs are refreshed to the
    newest position.
    """
    if max_size <= 0:
        return

    if request_id in pending_methods:
        del pending_methods[request_id]
    elif len(pending_methods) >= max_size and pending_methods:
        oldest_request_id = next(iter(pending_methods))
        del pending_methods[oldest_request_id]

    pending_methods[request_id] = method


def _prepare_webui_runtime(
    *,
    web_ui_port: Optional[int],
    web_ui_config: Optional[str],
    web_ui_restart: bool,
) -> Optional[Tuple[Any, Any, Any, Any, Any, Any]]:
    """Initialize Web UI runtime components and return runtime tuple.

    Returns:
        Tuple of (
            config,
            metrics_store,
            audit_logger,
            is_port_available,
            run_server,
            run_server_in_thread,
        ) or ``None`` when setup fails.
    """
    try:
        from mcpbridge_wrapper.webui.audit import AuditLogger
        from mcpbridge_wrapper.webui.config import WebUIConfig
        from mcpbridge_wrapper.webui.server import (
            is_port_available,
            run_server,
            run_server_in_thread,
        )
    except ImportError:
        print(
            "Error: Web UI dependencies not installed. "
            "Install with: pip install mcpbridge-wrapper[webui]",
            file=sys.stderr,
        )
        return None

    config = WebUIConfig(config_path=web_ui_config)
    config_file_port = config.port
    if web_ui_port is not None:
        if web_ui_config is not None and web_ui_port != config_file_port:  # pragma: no cover
            print(
                "Note: --web-ui-port overrides the port from --web-ui-config "
                f"({config_file_port} -> {web_ui_port}).",
                file=sys.stderr,
            )
        config._data["port"] = web_ui_port

    if web_ui_restart:
        if _restart_webui_listener(config.host, config.port):
            print(
                f"Web UI restart prepared on port {config.port}.",
                file=sys.stderr,
            )
        else:
            print(
                f"Error: Unable to free Web UI port {config.port} during restart.",
                file=sys.stderr,
            )
            return None

    # Shared metrics storage for multi-process visibility.
    from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore

    metrics = SharedMetricsStore()
    audit = AuditLogger(
        log_dir=config.audit_log_dir,
        max_file_size_mb=config.audit_max_file_size_mb,
        max_files=config.audit_max_files,
        capture_payload=config.audit_capture_payload,
    )
    audit.enabled = config.audit_enabled
    return config, metrics, audit, is_port_available, run_server, run_server_in_thread


def _effective_web_ui_port(
    *,
    web_ui_enabled: bool,
    web_ui_port: Optional[int],
    web_ui_config: Optional[str],
) -> Optional[int]:
    """Return the effective web UI port for the broker mismatch probe.

    When ``--web-ui-port`` is explicit, use it directly.  Otherwise derive the
    port from ``--web-ui-config`` (via WebUIConfig) so that the probe targets
    the same port the broker was configured with.  Falls back to 8080 if the
    webui extras are not installed.
    """
    if not web_ui_enabled:
        return None
    if web_ui_port is not None:
        return web_ui_port
    try:
        from mcpbridge_wrapper.webui.config import WebUIConfig

        return WebUIConfig(config_path=web_ui_config).port
    except ImportError:
        return 8080


def _build_broker_spawn_args(
    *,
    web_ui_enabled: bool,
    web_ui_port: Optional[int],
    web_ui_config: Optional[str],
    web_ui_restart: bool,
) -> list[str]:
    """Build daemon spawn args for broker auto-spawn flows."""
    spawn_args = ["--broker-daemon"]
    if not web_ui_enabled:
        return spawn_args

    spawn_args.append("--web-ui")
    if web_ui_restart:
        spawn_args.append("--web-ui-restart")
    if web_ui_port is not None:
        spawn_args.extend(["--web-ui-port", str(web_ui_port)])
    if web_ui_config is not None:
        spawn_args.extend(["--web-ui-config", web_ui_config])
    return spawn_args


def _read_running_broker_pid() -> Optional[int]:
    """Return the running broker PID from state files, or None when absent/stale."""
    from mcpbridge_wrapper.broker.types import BrokerConfig

    pid_file = BrokerConfig.default().pid_file
    if not pid_file.exists():
        return None

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None

    return pid if _pid_exists(pid) else None


def _is_broker_console_backend_ready(
    control: Dict[str, Any],
    broker_status: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Validate that a dashboard endpoint is backed by the dedicated broker host."""
    service_name = str(broker_status.get("service_name") or control.get("service_name") or "")
    if service_name != "broker-daemon":
        shown_name = service_name or "unknown service"
        return (
            False,
            f"Dashboard is served by '{shown_name}', not the dedicated broker host.",
        )

    if not bool(broker_status.get("available")):
        error = broker_status.get("error")
        if isinstance(error, str) and error:
            return False, error
        return False, "Dashboard is reachable but broker runtime status is unavailable."

    broker_payload = broker_status.get("broker")
    if not isinstance(broker_payload, dict):
        return False, "Dashboard is reachable but returned an invalid broker payload."

    return True, None


def _probe_broker_console_backend(runtime: Any) -> Tuple[bool, Optional[str]]:
    """Probe the dashboard API and report whether it is broker-backed."""
    from mcpbridge_wrapper.tui import BrokerTUIClient

    client = BrokerTUIClient(runtime)
    try:
        control, broker_status = client.probe_backend()
    except RuntimeError as exc:
        return False, str(exc)

    return _is_broker_console_backend_ready(control, broker_status)


def _recent_broker_events_hint(runtime: Any, max_lines: int = 3) -> str:
    """Return a compact broker log hint for startup diagnostics."""
    from mcpbridge_wrapper.tui import tail_log_lines

    lines = tail_log_lines(runtime.log_path, max_lines=max_lines)
    if not lines:
        return ""

    compact = " | ".join(line.strip() for line in lines if line.strip())
    if not compact:
        return ""
    return f" Recent broker events: {compact}"


def _broker_console_command() -> str:
    """Return the canonical attach command for the dedicated broker host."""
    return "`mcpbridge-wrapper --broker-console`"


def _broker_console_reset_command() -> str:
    """Return the canonical full-reset command for the dedicated broker host."""
    return "`mcpbridge-wrapper --broker-stop && mcpbridge-wrapper --broker-console`"


def _broker_console_restart_command() -> str:
    """Return the canonical restart-assisted recovery command."""
    return "`mcpbridge-wrapper --broker-console --web-ui-restart`"


def _format_listener_pid_summary(listener_pids: Set[int]) -> str:
    """Render a stable listener-PID summary for user-facing errors."""
    if not listener_pids:
        return "unknown listener"

    label = "PID" if len(listener_pids) == 1 else "PIDs"
    joined = ", ".join(str(pid) for pid in sorted(listener_pids))
    return f"listener {label} {joined}"


def _report_requested_dashboard_unavailable(
    *,
    runtime: Any,
    port: Optional[int],
    probe_error: Optional[str],
    running_broker_pid: Optional[int],
    listener_pids: Set[int],
) -> int:
    """Print one explicit remediation path for an unusable requested dashboard."""
    if port is not None and listener_pids and running_broker_pid is not None:
        print(
            "Error: Broker daemon is already running "
            f"(PID {running_broker_pid}), but Web UI port {port} is already occupied by "
            f"{_format_listener_pid_summary(listener_pids)}, so no broker-backed "
            f"dashboard is reachable at {runtime.base_url}. Stop the existing listener or "
            f"retry startup with {_broker_console_restart_command()}. If the port "
            f"becomes free and the dashboard is still unavailable, reset the dedicated "
            f"host with {_broker_console_reset_command()}.",
            file=sys.stderr,
        )
    elif running_broker_pid is not None:
        print(
            "Error: Broker daemon is already running "
            f"(PID {running_broker_pid}) but no broker-backed dashboard is reachable at "
            f"{runtime.base_url}. Restart the dedicated host with "
            f"{_broker_console_reset_command()}.",
            file=sys.stderr,
        )
    elif port is not None and listener_pids:
        print(
            f"Error: Web UI port {port} is already occupied by "
            f"{_format_listener_pid_summary(listener_pids)}. "
            f"Stop the existing listener or retry startup with "
            f"{_broker_console_restart_command()}.",
            file=sys.stderr,
        )
    elif port is not None:
        print(
            f"Error: Web UI port {port} is unavailable and no broker-backed dashboard is "
            f"reachable at {runtime.base_url}. Retry startup with "
            f"{_broker_console_restart_command()} or choose a different port.",
            file=sys.stderr,
        )
    else:
        print(
            f"Error: No broker-backed dashboard is reachable at {runtime.base_url}. "
            f"Restart the dedicated host with {_broker_console_reset_command()}.",
            file=sys.stderr,
        )

    if probe_error:
        print(f"Detail: {probe_error}", file=sys.stderr)
    return 1


def _report_existing_broker_dashboard(runtime: Any) -> int:
    """Report that the requested dashboard is already served by another broker host."""
    print(
        f"Error: Dashboard at {runtime.base_url} is already serving the dedicated broker host. "
        f"Use {_broker_console_command()} to attach, or stop the running broker with "
        "`mcpbridge-wrapper --broker-stop` before starting a new daemon.",
        file=sys.stderr,
    )
    return 1


def _spawn_broker_console_host(
    *,
    web_ui_port: Optional[int],
    web_ui_config: Optional[str],
    web_ui_restart: bool,
) -> subprocess.Popen:
    """Spawn a dedicated broker host detached from the current terminal."""
    from mcpbridge_wrapper.broker.types import BrokerConfig

    broker_config = BrokerConfig.default()
    state_dir = broker_config.pid_file.parent
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "broker.log"

    spawn_args = _build_broker_spawn_args(
        web_ui_enabled=True,
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
        web_ui_restart=web_ui_restart,
    )
    cmd = [sys.executable, "-m", "mcpbridge_wrapper", *spawn_args]

    log_handle = log_path.open("ab")
    try:
        return subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()


def _wait_for_broker_console_backend(
    runtime: Any,
    *,
    timeout_seconds: float = 10.0,
    poll_interval_seconds: float = 0.1,
    child_process: Optional[subprocess.Popen] = None,
) -> Optional[str]:
    """Wait for a broker-backed dashboard endpoint, returning an error on failure."""
    deadline = time.monotonic() + timeout_seconds
    last_error = f"Timed out waiting for a broker-backed dashboard at {runtime.base_url}."

    while time.monotonic() < deadline:
        ready, error = _probe_broker_console_backend(runtime)
        if ready:
            return None

        if error:
            last_error = error

        if child_process is not None and child_process.poll() is not None:
            return (
                f"Broker host exited before the dashboard was ready at {runtime.base_url}. "
                f"Last probe error: {last_error}.{_recent_broker_events_hint(runtime)}"
            )

        time.sleep(poll_interval_seconds)

    return (
        f"Timed out waiting for a broker-backed dashboard at {runtime.base_url}. "
        f"Last probe error: {last_error}.{_recent_broker_events_hint(runtime)}"
    )


def _run_broker_console(
    *,
    web_ui_port: Optional[int],
    web_ui_config: Optional[str],
    web_ui_restart: bool,
) -> int:
    """Start or reuse the recommended dedicated broker host and attach the TUI."""
    from mcpbridge_wrapper.tui import build_tui_runtime, run_tui

    def _run_console_tui() -> int:
        try:
            return run_tui(runtime)
        except KeyboardInterrupt:
            return 0

    runtime = build_tui_runtime(
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
    )

    ready, error = _probe_broker_console_backend(runtime)
    if ready:
        return _run_console_tui()

    effective_port = _effective_web_ui_port(
        web_ui_enabled=True,
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
    )
    listener_pids: Set[int] = set()
    if effective_port is not None and not web_ui_restart:
        listener_pids = _find_listener_pids_for_port(effective_port)

    running_pid = _read_running_broker_pid()
    if running_pid is not None:
        return _report_requested_dashboard_unavailable(
            runtime=runtime,
            port=effective_port,
            probe_error=error,
            running_broker_pid=running_pid,
            listener_pids=listener_pids,
        )

    if listener_pids:
        return _report_requested_dashboard_unavailable(
            runtime=runtime,
            port=effective_port,
            probe_error=error,
            running_broker_pid=None,
            listener_pids=listener_pids,
        )

    child_process = _spawn_broker_console_host(
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
        web_ui_restart=web_ui_restart,
    )
    wait_error = _wait_for_broker_console_backend(runtime, child_process=child_process)
    if wait_error is not None:
        print(f"Error: {wait_error}", file=sys.stderr)
        return 1

    return _run_console_tui()


def main() -> int:
    """Main entry point for the mcpbridge-wrapper command.

    Creates a bridge to xcrun mcpbridge, starts stdin forwarding in a daemon
    thread, reads stdout via a daemon thread into a queue, processes each
    response line through process_response_line() for MCP compliance transformation,
    and outputs unbuffered results to stdout.

    Supports optional --web-ui flag to start a monitoring dashboard.
    Supports optional --tui flag for standalone broker terminal monitoring.
    Supports optional --doctor flag for broker workflow diagnostics.
    Supports optional --broker-daemon flag to start a persistent broker host.
    Supports optional --broker flag for proxy mode.

    Returns:
        Exit code from the bridge process (0 for success)
    """
    # Parse web UI args from command line
    all_args = sys.argv[1:] if len(sys.argv) > 1 else []
    try:
        (
            web_ui_enabled,
            web_ui_only,
            web_ui_restart,
            web_ui_port,
            web_ui_config,
            after_webui_args,
        ) = _parse_webui_args(all_args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    tui_enabled, after_tui_args = _parse_tui_args(after_webui_args)
    broker_console, after_console_args = _parse_broker_console_args(after_tui_args)
    doctor_enabled, after_doctor_args = _parse_doctor_args(after_console_args)
    broker_daemon, broker_connect, broker_spawn, broker_status, broker_stop, bridge_args = (
        _parse_broker_args(after_doctor_args)
    )

    if tui_enabled and broker_console:
        print(
            "Error: --tui cannot be combined with --broker-console.",
            file=sys.stderr,
        )
        return 2

    if tui_enabled and web_ui_enabled:
        print(
            "Error: --tui cannot be combined with --web-ui flags. "
            "Use --web-ui-port/--web-ui-config to target an existing dashboard.",
            file=sys.stderr,
        )
        return 2

    if tui_enabled and (broker_daemon or broker_connect or broker_status or broker_stop):
        print("Error: --tui cannot be combined with broker mode flags.", file=sys.stderr)
        return 2

    if tui_enabled and bridge_args:
        print("Error: --tui does not accept bridge arguments.", file=sys.stderr)
        return 2

    if broker_console and (broker_daemon or broker_connect or broker_status or broker_stop):
        print(
            "Error: --broker-console cannot be combined with broker mode flags.",
            file=sys.stderr,
        )
        return 2

    if broker_console and bridge_args:
        print("Error: --broker-console does not accept bridge arguments.", file=sys.stderr)
        return 2

    if doctor_enabled and web_ui_enabled:
        print(
            "Error: --doctor cannot be combined with --web-ui flags. "
            "Use --web-ui-port/--web-ui-config to target an existing dashboard.",
            file=sys.stderr,
        )
        return 2

    if doctor_enabled and (tui_enabled or broker_console):
        print(
            "Error: --doctor cannot be combined with --tui or --broker-console.",
            file=sys.stderr,
        )
        return 2

    if doctor_enabled and (broker_daemon or broker_connect or broker_status or broker_stop):
        print("Error: --doctor cannot be combined with broker mode flags.", file=sys.stderr)
        return 2

    if doctor_enabled and bridge_args:
        print("Error: --doctor does not accept bridge arguments.", file=sys.stderr)
        return 2

    if web_ui_only and (broker_console or broker_daemon or broker_connect):
        print(
            "Error: --web-ui-only cannot be combined with broker mode flags.",
            file=sys.stderr,
        )
        return 2

    if tui_enabled:
        from mcpbridge_wrapper.tui import build_tui_runtime, run_tui

        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print("Error: --tui requires an interactive terminal.", file=sys.stderr)
            return 2

        tui_runtime = build_tui_runtime(
            web_ui_port=web_ui_port,
            web_ui_config=web_ui_config,
        )
        try:
            return run_tui(tui_runtime)
        except KeyboardInterrupt:
            return 0

    if broker_console:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print("Error: --broker-console requires an interactive terminal.", file=sys.stderr)
            return 2
        return _run_broker_console(
            web_ui_port=web_ui_port,
            web_ui_config=web_ui_config,
            web_ui_restart=web_ui_restart,
        )

    if doctor_enabled:
        from mcpbridge_wrapper.doctor import run_doctor

        return run_doctor(
            web_ui_port=web_ui_port,
            web_ui_config=web_ui_config,
        )

    # --broker-status: print broker daemon status and exit
    if broker_status:
        from mcpbridge_wrapper import __version__
        from mcpbridge_wrapper.broker.types import BrokerConfig

        broker_config = BrokerConfig.default()
        print(f"Proxy version: {__version__}")
        print(f"PID file:      {broker_config.pid_file}")
        print(f"Socket:        {broker_config.socket_path}")
        print(f"Version file:  {broker_config.version_file}")

        pid: Optional[int] = None
        if broker_config.pid_file.exists():
            try:
                pid = int(broker_config.pid_file.read_text().strip())
                os.kill(pid, 0)
                print(f"Daemon PID:    {pid} (running)")
            except (ValueError, ProcessLookupError):
                print("Daemon PID:    (not running)")
                pid = None
            except PermissionError:
                print(f"Daemon PID:    {pid} (running, different user)")
        else:
            print("Daemon PID:    (not running)")

        daemon_version: Optional[str] = None
        if broker_config.version_file.exists():
            with contextlib.suppress(OSError):
                daemon_version = broker_config.version_file.read_text().strip()
        if daemon_version:
            print(f"Daemon version: {daemon_version}")
            if daemon_version != __version__:
                print(f"WARNING: version mismatch! proxy={__version__}, daemon={daemon_version}")
        else:
            print("Daemon version: (unknown)")
        return 0

    # --broker-stop: stop running broker daemon and exit
    if broker_stop:
        from mcpbridge_wrapper.broker.types import BrokerConfig

        broker_config = BrokerConfig.default()
        pid_file = broker_config.pid_file
        if not pid_file.exists():
            print("Broker is not running (no PID file).")
            return 0
        try:
            pid_val = int(pid_file.read_text().strip())
        except (ValueError, OSError):
            print("Corrupt PID file; cleaning up.", file=sys.stderr)
            for p in (pid_file, broker_config.socket_path, broker_config.version_file):
                p.unlink(missing_ok=True)
            return 0

        stopped = False
        try:
            os.kill(pid_val, signal.SIGTERM)
            print(f"Sent SIGTERM to broker (PID {pid_val}).")
        except ProcessLookupError:
            print(f"Broker (PID {pid_val}) is not running; cleaning up files.")
            stopped = True
        except PermissionError:
            print(
                f"Error: Cannot stop broker (PID {pid_val}): permission denied.",
                file=sys.stderr,
            )
            return 1

        # Wait up to 3 seconds for clean exit.
        if not stopped:
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                try:
                    os.kill(pid_val, 0)
                except ProcessLookupError:
                    stopped = True
                    break
                time.sleep(0.1)

            # Final probe in case process exited just after timeout boundary.
            if not stopped:
                try:
                    os.kill(pid_val, 0)
                except ProcessLookupError:
                    stopped = True

        if not stopped:
            print(
                "Error: Broker did not stop within 3 seconds; state files were left intact.",
                file=sys.stderr,
            )
            return 1

        for p in (pid_file, broker_config.socket_path, broker_config.version_file):
            p.unlink(missing_ok=True)
        print("Broker stopped and files cleaned up.")
        return 0

    # Broker daemon mode: long-lived upstream + Unix socket server
    if broker_daemon:
        import asyncio

        from mcpbridge_wrapper.broker.daemon import BrokerDaemon
        from mcpbridge_wrapper.broker.transport import UnixSocketServer
        from mcpbridge_wrapper.broker.types import BrokerConfig

        stop_requested = threading.Event()
        daemon: Optional[BrokerDaemon] = None
        config = None
        metrics = None
        audit = None

        def get_broker_status() -> Optional[Dict[str, Any]]:
            """Return live broker runtime status for explicit frontend consumers."""
            if daemon is None:
                return None
            return daemon.status()

        if web_ui_enabled:
            runtime = _prepare_webui_runtime(
                web_ui_port=web_ui_port,
                web_ui_config=web_ui_config,
                web_ui_restart=web_ui_restart,
            )
            if runtime is None:
                return 1

            (
                config,
                metrics,
                audit,
                is_port_available,
                _run_server,
                run_server_in_thread,
            ) = runtime

            if not is_port_available(config.host, config.port):
                from mcpbridge_wrapper.tui import build_tui_runtime

                dashboard_runtime = build_tui_runtime(
                    web_ui_port=config.port,
                    web_ui_config=web_ui_config,
                )
                ready, error = _probe_broker_console_backend(dashboard_runtime)
                if ready:
                    audit.close()
                    return _report_existing_broker_dashboard(dashboard_runtime)

                running_pid = _read_running_broker_pid()
                listener_pids = _find_listener_pids_for_port(config.port)
                audit.close()
                return _report_requested_dashboard_unavailable(
                    runtime=dashboard_runtime,
                    port=config.port,
                    probe_error=error,
                    running_broker_pid=running_pid,
                    listener_pids=listener_pids,
                )
            else:

                def request_broker_shutdown() -> None:
                    """Request broker daemon shutdown after replying to HTTP control call."""
                    stop_requested.set()
                    if daemon is not None:
                        daemon.request_shutdown()

                _ = run_server_in_thread(
                    config,
                    metrics,
                    audit,
                    service_name="broker-daemon",
                    request_stop=request_broker_shutdown,
                    broker_status_provider=get_broker_status,
                )
                print(
                    f"Web UI dashboard started at http://{config.host}:{config.port}",
                    file=sys.stderr,
                )

        broker_config = BrokerConfig.default()
        daemon = BrokerDaemon(broker_config)
        if stop_requested.is_set():
            daemon.request_shutdown()

        transport = UnixSocketServer(
            broker_config,
            daemon,
            metrics=metrics,
            audit=audit,
        )
        daemon._transport = transport
        try:
            asyncio.run(daemon.run_forever())
        except KeyboardInterrupt:
            pass
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        finally:
            if audit is not None:
                audit.close()
        return 0

    # Broker proxy mode: connect (or spawn-then-connect) to persistent broker
    if broker_connect:
        import asyncio

        from mcpbridge_wrapper.broker.proxy import BrokerProxy
        from mcpbridge_wrapper.broker.types import BrokerConfig

        broker_config = BrokerConfig.default()
        proxy = BrokerProxy(
            broker_config,
            auto_spawn=broker_spawn,
            connect_timeout=10.0,
            spawn_args=_build_broker_spawn_args(
                web_ui_enabled=web_ui_enabled,
                web_ui_port=web_ui_port,
                web_ui_config=web_ui_config,
                web_ui_restart=web_ui_restart,
            ),
            web_ui_port=_effective_web_ui_port(
                web_ui_enabled=web_ui_enabled,
                web_ui_port=web_ui_port,
                web_ui_config=web_ui_config,
            ),
        )
        try:
            asyncio.run(proxy.run())
        except TimeoutError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            pass
        return 0

    # Initialize web UI components if enabled
    config = None
    metrics = None
    audit = None

    if web_ui_enabled:
        runtime = _prepare_webui_runtime(
            web_ui_port=web_ui_port,
            web_ui_config=web_ui_config,
            web_ui_restart=web_ui_restart,
        )
        if runtime is None:
            return 1

        (
            config,
            metrics,
            audit,
            is_port_available,
            run_server,
            run_server_in_thread,
        ) = runtime

        if web_ui_only:
            if not is_port_available(config.host, config.port):
                print(
                    f"Error: Web UI port {config.port} is already in use. "
                    "Stop the existing process and retry.",
                    file=sys.stderr,
                )
                audit.close()
                return 1
            print(
                f"Web UI dashboard started at http://{config.host}:{config.port}",
                file=sys.stderr,
            )
            try:
                # Standalone mode keeps only the dashboard process running.
                run_server(config, metrics, audit)
            except KeyboardInterrupt:
                pass
            finally:
                audit.close()
            return 0

        # metrics is SharedMetricsStore but server expects MetricsCollector
        # They have compatible interfaces for the Web UI read operations
        if not is_port_available(config.host, config.port):
            print(
                f"Warning: Web UI port {config.port} is already in use. "
                "Skipping Web UI startup — MCP bridge will run without the dashboard.",
                file=sys.stderr,
            )
            if web_ui_port is not None and web_ui_config is not None:  # pragma: no cover
                print(
                    "Hint: You passed both --web-ui-port and --web-ui-config. "
                    "--web-ui-port takes precedence; remove it to use the config file port.",
                    file=sys.stderr,
                )
        else:
            _ = run_server_in_thread(config, metrics, audit)
            print(
                f"Web UI dashboard started at http://{config.host}:{config.port}",
                file=sys.stderr,
            )

    # Create bridge with forwarded command-line arguments
    args = bridge_args if bridge_args else None
    bridge = create_bridge(args)

    # Verify bridge started successfully
    if bridge.poll() is not None:
        print("Error: Failed to start mcpbridge", file=sys.stderr)
        return 1

    exit_code = 0
    global _seen_initialize, _seen_tools_request

    # Track pending requests for metrics: request_id -> (tool_name, start_time)
    pending_requests: Dict[str, Tuple[str, float]] = {}

    # Track pending request methods for error normalization: request_id -> method
    # This covers ALL request types (not just tools/call) so that non-tool method
    # responses can be normalized to standard JSON-RPC errors (BUG-T7).
    pending_methods: Dict[str, str] = {}
    stdin_closed = threading.Event()

    # Create request handler callback for stdin forwarder
    def on_request(line: str) -> None:
        """Handle request line from stdin for metrics tracking."""
        try:
            from mcpbridge_wrapper.schemas import MCPRequest

            req = MCPRequest.model_validate_json(line)
            request_id = str(req.id) if req.id is not None else None
            method = req.method

            # Track method for ALL requests with an id (enables error normalization)
            if request_id is not None and method is not None:
                _track_pending_method(
                    pending_methods,
                    request_id=request_id,
                    method=method,
                    max_size=MAX_PENDING_METHODS,
                )

            # This callback sees only stdin traffic (client -> wrapper), so client
            # identity capture is intentionally limited to inbound initialize calls.
            if method == "initialize" and metrics is not None:
                client_info = req.get_client_info()
                if client_info is not None:
                    metrics.set_client_info(client_info.name, client_info.version)
                else:
                    metrics.set_client_info("unknown", "unknown")

            if metrics is None:
                return

            tool_name = _extract_tool_name(line)
            if tool_name and request_id and method is not None:
                start_time = time.time()
                metrics.record_request(tool_name, request_id=request_id)
                pending_requests[request_id] = (tool_name, start_time)

                # Capture parameter key names when feature flag is enabled
                if (
                    config is not None
                    and config.capture_params
                    and req.params is not None
                    and req.params.arguments is not None
                ):
                    param_keys = list(req.params.arguments.keys())
                    metrics.record_param_keys(tool_name, param_keys)

        except Exception:
            pass

    def on_stdin_closed() -> None:
        """Terminate upstream bridge when client stdin reaches EOF."""
        if stdin_closed.is_set():
            return
        stdin_closed.set()

        # Forward EOF upstream first so mcpbridge can finish pending responses.
        if bridge.stdin is not None:
            with contextlib.suppress(BrokenPipeError, OSError, ValueError):
                bridge.stdin.close()

        drain_deadline = time.monotonic() + STDIN_EOF_DRAIN_TIMEOUT_SECONDS
        while bridge.poll() is None and time.monotonic() < drain_deadline:
            if not pending_methods:
                break
            time.sleep(STDIN_EOF_DRAIN_POLL_INTERVAL_SECONDS)

        terminate_bridge_process(bridge, grace_period=5.0)

    # Start stdin forwarding in a daemon thread (with request tracking)
    _ = run_stdin_forwarder(
        bridge,
        on_request=on_request,
        on_stdin_closed=on_stdin_closed,
    )

    # Start stdout reader in a daemon thread with queue
    stdout_thread, output_queue = run_stdout_reader(bridge)

    # Set up signal handlers for clean shutdown
    def signal_handler(signum: int, frame: object) -> None:
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        pass  # Let the main loop handle cleanup via queue

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Process lines from the queue until EOF (None sentinel)
        while True:
            line = output_queue.get()
            if line is None:
                # EOF reached - bridge closed stdout
                break

            # Track initialization for diagnostics
            if '"method":"initialize"' in line.replace(" ", "") or '"method": "initialize"' in line:
                _seen_initialize = True
            if '"method":"tools/list"' in line.replace(" ", "") or '"method": "tools/list"' in line:
                _seen_tools_request = True

            # Extract request_id for response matching and method lookup
            request_id = _extract_request_id(line)

            # Look up the originating method for method-aware error normalization
            response_method = pending_methods.pop(request_id, None) if request_id else None

            # Transform the response line for MCP compliance (with method context)
            processed = process_response_line(line, method=response_method)

            # Record response metrics and audit (requests are tracked in on_request)
            if metrics is not None and request_id and request_id in pending_requests:
                # This is a response to a tracked request
                pending_tool_name, pending_start_time = pending_requests.pop(request_id)
                latency_ms = (time.time() - pending_start_time) * 1000.0
                is_error, error_code, error_message = _parse_error_info(line)
                metrics.record_response(
                    pending_tool_name,
                    request_id=request_id,
                    error=is_error,
                    latency_ms=latency_ms,
                    error_code=error_code,
                    error_message=error_message,
                )

                if audit is not None:
                    audit.log(
                        tool_name=pending_tool_name,
                        request_id=request_id,
                        latency_ms=latency_ms,
                        error=error_message if is_error else None,
                        error_code=error_code if is_error else None,
                        direction="response",
                    )

            # Output unbuffered (flush=True via write + flush)
            sys.stdout.write(processed)
            # Ensure newline if line doesn't end with one
            if processed and not processed.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        # User interrupted - clean shutdown will proceed in finally block
        pass
    finally:
        # Clean up bridge and get exit code
        exit_code = cleanup_bridge(bridge)

        # Diagnostic: if we saw initialize and tools/list but bridge exited cleanly (0)
        # without responding to tools/list, Xcode Tools MCP is likely not enabled
        if _seen_initialize and _seen_tools_request and exit_code == 0:
            check_xcode_tools_enabled()

        # Clean up audit logger
        if audit is not None:
            audit.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
