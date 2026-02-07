"""mcpbridge-wrapper - Protocol compatibility wrapper for Xcode's MCP bridge."""

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    forward_stdin,
    read_stdout,
    read_stdout_line,
    run_stdin_forwarder,
    run_stdout_reader,
    verify_bridge_started,
)

__version__ = "1.0.0"
__all__ = [
    "create_bridge",
    "cleanup_bridge",
    "forward_stdin",
    "read_stdout",
    "read_stdout_line",
    "run_stdin_forwarder",
    "run_stdout_reader",
    "verify_bridge_started",
]
