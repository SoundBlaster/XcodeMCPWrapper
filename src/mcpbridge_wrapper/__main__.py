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
) -> Tuple[bool, bool, bool, list]:
    """Parse broker arguments from command-line args.

    Extracts ``--broker-daemon`` and ``--broker`` flags and returns them
    along with the remaining args to forward to the bridge. Broker-only flags
    are *never* forwarded to
    ``xcrun mcpbridge``.

    ``--broker`` is the recommended flag: it auto-detects whether a daemon is
    already running and spawns one if needed.

    Args:
        args: Command-line arguments list.

    Returns:
        Tuple of (broker_daemon, broker_connect, broker_spawn, remaining_args).
    """
    broker_daemon = False
    broker_connect = False
    broker_spawn = False
    remaining = []

    for arg in args:
        if arg == "--broker-daemon":
            broker_daemon = True
        elif arg == "--broker":
            # Recommended flag: auto-detect (spawn if needed, then connect).
            broker_spawn = True
            broker_connect = True
        else:
            remaining.append(arg)

    return broker_daemon, broker_connect, broker_spawn, remaining


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


def main() -> int:
    """Main entry point for the mcpbridge-wrapper command.

    Creates a bridge to xcrun mcpbridge, starts stdin forwarding in a daemon
    thread, reads stdout via a daemon thread into a queue, processes each
    response line through process_response_line() for MCP compliance transformation,
    and outputs unbuffered results to stdout.

    Supports optional --web-ui flag to start a monitoring dashboard.
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

    broker_daemon, broker_connect, broker_spawn, bridge_args = _parse_broker_args(after_webui_args)

    if web_ui_only and (broker_daemon or broker_connect):
        print(
            "Error: --web-ui-only cannot be combined with broker mode flags.",
            file=sys.stderr,
        )
        return 2

    # Broker daemon mode: long-lived upstream + Unix socket server
    if broker_daemon:
        import asyncio

        from mcpbridge_wrapper.broker.daemon import BrokerDaemon
        from mcpbridge_wrapper.broker.transport import UnixSocketServer
        from mcpbridge_wrapper.broker.types import BrokerConfig

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
                _run_server,
                run_server_in_thread,
            ) = runtime

            if not is_port_available(config.host, config.port):
                print(
                    f"Warning: Web UI port {config.port} is already in use. "
                    "Skipping Web UI startup — broker daemon will run without the dashboard.",
                    file=sys.stderr,
                )
            else:
                _ = run_server_in_thread(config, metrics, audit)
                print(
                    f"Web UI dashboard started at http://{config.host}:{config.port}",
                    file=sys.stderr,
                )

        broker_config = BrokerConfig.default()
        daemon = BrokerDaemon(broker_config)
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
