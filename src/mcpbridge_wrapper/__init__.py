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
from mcpbridge_wrapper.transform import (
    extract_text_content,
    inject_structured_content,
    is_json_line,
    needs_transformation,
    parse_json_safe,
    parse_structured_content,
    parse_structured_content_with_fallback,
    process_response_line,
)

__version__ = "1.0.0"
__all__ = [
    # Bridge functions
    "create_bridge",
    "cleanup_bridge",
    "forward_stdin",
    "read_stdout",
    "read_stdout_line",
    "run_stdin_forwarder",
    "run_stdout_reader",
    "verify_bridge_started",
    # Transform functions
    "process_response_line",
    "is_json_line",
    "parse_json_safe",
    "needs_transformation",
    "extract_text_content",
    "parse_structured_content",
    "parse_structured_content_with_fallback",
    "inject_structured_content",
]
