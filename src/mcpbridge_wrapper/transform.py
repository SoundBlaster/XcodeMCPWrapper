"""
Response transformation engine for mcpbridge-wrapper.

This module provides functions to detect and transform MCP responses
to ensure compliance with the MCP specification.
"""

import json
from typing import Any


def is_json_line(line: str) -> bool:
    """
    Detect whether a line is valid JSON or plain text.

    Args:
        line: The input line to check.

    Returns:
        True if the line is valid JSON, False otherwise.
    """
    if not line or not line.strip():
        return False

    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        return False


def parse_json_safe(line: str) -> tuple[bool, Any]:
    """
    Safely parse a JSON line, returning success status and result.

    Args:
        line: The input line to parse.

    Returns:
        A tuple of (success: bool, result: Any). On success, result is the
        parsed JSON value. On failure, result is the original line.
    """
    try:
        parsed = json.loads(line)
        return (True, parsed)
    except json.JSONDecodeError:
        return (False, line)
