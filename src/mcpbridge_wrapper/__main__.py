"""Entry point for mcpbridge-wrapper."""

import json
import signal
import sys
import time
from typing import Optional, Tuple

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


def _parse_webui_args(args: list) -> Tuple[bool, Optional[int], Optional[str], list]:
    """Parse web UI arguments from command-line args.

    Extracts --web-ui, --web-ui-port, and --web-ui-config flags and
    returns them along with the remaining args to forward to the bridge.

    Args:
        args: Command-line arguments list.

    Returns:
        Tuple of (web_ui_enabled, port_or_none, config_path_or_none, remaining_args).
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
            port = int(args[i + 1])
            i += 2
        elif args[i].startswith("--web-ui-port="):
            port = int(args[i].split("=", 1)[1])
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

    Args:
        line: A line from the bridge output.

    Returns:
        The tool name if found, None otherwise.
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    # Check for tool name in params (MCP tool/call format)
    # Format: {"method": "tools/call", "params": {"name": "ToolName", ...}}
    params = data.get("params")
    if isinstance(params, dict):
        # For tools/call, the tool name is in params.name
        name = params.get("name")
        if isinstance(name, str) and name not in ("initialize", "tools/list"):
            return name

    # Check for method in request (direct tool call format)
    method = data.get("method")
    if isinstance(method, str) and not method.startswith("tools/"):
        return method

    # Check for tool name in result (response format)
    result = data.get("result")
    if isinstance(result, dict):
        name = result.get("name") or result.get("toolName")
        if isinstance(name, str):
            return name

    return None


def _extract_request_id(line: str) -> Optional[str]:
    """Extract the JSON-RPC request ID from a line.

    Args:
        line: A line from the bridge output.

    Returns:
        The request ID as a string if found, None otherwise.
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None

    if isinstance(data, dict) and "id" in data:
        return str(data["id"])
    return None


def _has_error(line: str) -> bool:
    """Check if a JSON-RPC response contains an error.

    Args:
        line: A line from the bridge output.

    Returns:
        True if the line contains an error response.
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return False

    return isinstance(data, dict) and "error" in data


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
    web_ui_enabled, web_ui_port, web_ui_config, bridge_args = _parse_webui_args(all_args)

    # Initialize web UI components if enabled
    metrics = None
    audit = None

    if web_ui_enabled:
        try:
            from mcpbridge_wrapper.webui.audit import AuditLogger
            from mcpbridge_wrapper.webui.config import WebUIConfig
            from mcpbridge_wrapper.webui.metrics import MetricsCollector
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

        metrics = MetricsCollector(
            window_seconds=config.metrics_window_seconds,
            max_datapoints=config.metrics_max_datapoints,
        )
        audit = AuditLogger(
            log_dir=config.audit_log_dir,
            max_file_size_mb=config.audit_max_file_size_mb,
            max_files=config.audit_max_files,
        )
        audit.enabled = config.audit_enabled

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

    # Start stdin forwarding in a daemon thread
    _ = run_stdin_forwarder(bridge)  # Thread runs in background, no direct reference needed

    # Start stdout reader in a daemon thread with queue
    stdout_thread, output_queue = run_stdout_reader(bridge)

    # Set up signal handlers for clean shutdown
    def signal_handler(signum: int, frame: object) -> None:
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        pass  # Let the main loop handle cleanup via queue

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    exit_code = 0
    global _seen_initialize, _seen_tools_request

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

            # Metrics and audit hooks
            tool_name = None
            request_id = None
            start_time = None
            if metrics is not None:
                tool_name = _extract_tool_name(line)
                request_id = _extract_request_id(line)
                if tool_name:
                    start_time = time.time()
                    metrics.record_request(tool_name, request_id=request_id)

            # Transform the response line for MCP compliance
            processed = process_response_line(line)

            # Record response metrics and audit
            if metrics is not None and tool_name and start_time is not None:
                latency_ms = (time.time() - start_time) * 1000.0
                is_error = _has_error(line)
                metrics.record_response(
                    tool_name,
                    request_id=request_id,
                    error=is_error,
                    latency_ms=latency_ms,
                )
                if audit is not None:
                    audit.log(
                        tool_name=tool_name,
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
