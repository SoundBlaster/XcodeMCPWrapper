"""
Response transformation engine for mcpbridge-wrapper.

This module provides functions to detect and transform MCP responses
to ensure compliance with the MCP specification.
"""

import json


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
