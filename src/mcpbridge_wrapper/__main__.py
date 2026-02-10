"""Entry point for mcpbridge-wrapper."""

import signal
import sys
import time
from typing import Dict, Optional, Tuple

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    run_stdin_forwarder,
    run_stdout_reader,
)
from mcpbridge_wrapper.transform import process_response_line

# Diagnostic tracking
_seen_initialize = False
_seen_tools_request = False
_tools_response_timeout = False


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


def _parse_webui_args(args: list) -> Tuple[bool, Optional[int], Optional[str], list]:
    """Parse web UI arguments from command-line args.

    Extracts --web-ui, --web-ui-port, and --web-ui-config flags and
    returns them along with the remaining args to forward to the bridge.

    Args:
        args: Command-line arguments list.

    Returns:
        Tuple of (web_ui_enabled, port_or_none, config_path_or_none, remaining_args).

    Raises:
        ValueError: If --web-ui-port is not an integer in [1, 65535].
    """
    web_ui = False
    port: Optional[int] = None
    config_path: Optional[str] = None
    remaining = []

    i = 0
    while i < len(args):
        if args[i] == "--web-ui":
            web_ui = True
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

    return web_ui, port, config_path, remaining


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


def _has_error(line: str) -> bool:
    """Check if a JSON-RPC response contains an error.

    Args:
        line: A line from the bridge output.

    Returns:
        True if the line contains an error response.
    """
    try:
        from mcpbridge_wrapper.schemas import MCPResponse

        resp = MCPResponse.model_validate_json(line)
        return resp.has_error()
    except Exception:
        return False


def main() -> int:
    """Main entry point for the mcpbridge-wrapper command.

    Creates a bridge to xcrun mcpbridge, starts stdin forwarding in a daemon
    thread, reads stdout via a daemon thread into a queue, processes each
    response line through process_response_line() for MCP compliance transformation,
    and outputs unbuffered results to stdout.

    Supports optional --web-ui flag to start a monitoring dashboard.

    Returns:
        Exit code from the bridge process (0 for success)
    """
    # Parse web UI args from command line
    all_args = sys.argv[1:] if len(sys.argv) > 1 else []
    try:
        web_ui_enabled, web_ui_port, web_ui_config, bridge_args = _parse_webui_args(all_args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    # Initialize web UI components if enabled
    metrics = None
    audit = None

    if web_ui_enabled:
        try:
            from mcpbridge_wrapper.webui.audit import AuditLogger
            from mcpbridge_wrapper.webui.config import WebUIConfig
            from mcpbridge_wrapper.webui.server import run_server_in_thread
        except ImportError:
            print(
                "Error: Web UI dependencies not installed. "
                "Install with: pip install mcpbridge-wrapper[webui]",
                file=sys.stderr,
            )
            return 1

        config = WebUIConfig(config_path=web_ui_config)
        if web_ui_port is not None:
            config._data["port"] = web_ui_port

        # Use shared metrics store for multi-process support
        from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore

        metrics = SharedMetricsStore()
        audit = AuditLogger(
            log_dir=config.audit_log_dir,
            max_file_size_mb=config.audit_max_file_size_mb,
            max_files=config.audit_max_files,
        )
        audit.enabled = config.audit_enabled

        # metrics is SharedMetricsStore but server expects MetricsCollector
        # They have compatible interfaces for the Web UI read operations
        _ = run_server_in_thread(config, metrics, audit)  # type: ignore[arg-type]

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

    # Create request handler callback for stdin forwarder
    def on_request(line: str) -> None:
        """Handle request line from stdin for metrics tracking."""
        if metrics is None:
            return
        try:
            tool_name = _extract_tool_name(line)
            request_id = _extract_request_id(line)

            if tool_name and request_id:
                # Verify this is actually a request (has method)
                from mcpbridge_wrapper.schemas import MCPRequest

                req = MCPRequest.model_validate_json(line)
                if req.method is not None:
                    start_time = time.time()
                    metrics.record_request(tool_name, request_id=request_id)
                    pending_requests[request_id] = (tool_name, start_time)

        except Exception:
            pass

    # Start stdin forwarding in a daemon thread (with request tracking)
    _ = run_stdin_forwarder(bridge, on_request=on_request)

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

            # Extract request_id for response matching
            request_id = _extract_request_id(line) if metrics is not None else None

            # Transform the response line for MCP compliance
            processed = process_response_line(line)

            # Record response metrics and audit (requests are tracked in on_request)
            if metrics is not None and request_id and request_id in pending_requests:
                # This is a response to a tracked request
                pending_tool_name, pending_start_time = pending_requests.pop(request_id)
                latency_ms = (time.time() - pending_start_time) * 1000.0
                is_error = _has_error(line)
                metrics.record_response(
                    pending_tool_name,
                    request_id=request_id,
                    error=is_error,
                    latency_ms=latency_ms,
                )

                if audit is not None:
                    audit.log(
                        tool_name=pending_tool_name,
                        request_id=request_id,
                        latency_ms=latency_ms,
                        error=str(is_error) if is_error else None,
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
