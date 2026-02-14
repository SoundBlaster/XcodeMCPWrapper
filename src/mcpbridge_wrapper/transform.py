"""
Response transformation engine for mcpbridge-wrapper.

This module provides functions to detect and transform MCP responses
to ensure compliance with the MCP specification.

Note on Output Buffering:
    The process_response_line() function returns processed lines that
    should be output with immediate flushing (flush=True). This ensures
    MCP responses are delivered to clients without buffering delays,
    which is critical for real-time protocol compliance (PRD §3.1 FR9).

    Example usage in main loop:
        for line in read_stdout(bridge):
            processed = process_response_line(line)
            sys.stdout.write(processed)
            sys.stdout.flush()  # Required: immediate flush
"""

import json
from typing import Any, Optional


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


def needs_transformation(data: Any) -> bool:
    """
    Check if an MCP response needs structuredContent transformation.

    A response needs transformation if it has a 'result' dict with 'content'
    but is missing the 'structuredContent' field.

    Args:
        data: The parsed JSON data to check.

    Returns:
        True if the response needs transformation, False otherwise.
    """
    if not isinstance(data, dict):
        return False

    result = data.get("result")
    if not isinstance(result, dict):
        return False

    if "content" not in result:
        return False

    if "structuredContent" in result:
        return False

    content = result.get("content")
    if not isinstance(content, list):
        return False

    # Empty content arrays need structuredContent: {} injected for strict clients
    if len(content) == 0:
        return True

    # Non-empty content: only transform if there is a text item to extract
    return extract_text_content(content) is not None


def extract_text_content(content: list) -> Optional[str]:
    """
    Extract the text field from the first content item with type "text".

    Args:
        content: A list of content items from an MCP response.

    Returns:
        The text string if found, None otherwise.
    """
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str):
                return text
    return None


def parse_structured_content(text: str) -> Any:
    """
    Parse extracted text content as JSON.

    Args:
        text: The text content to parse (typically from extract_text_content).

    Returns:
        The parsed JSON value (dict, list, str, int, float, bool, or None).

    Raises:
        json.JSONDecodeError: If the text is not valid JSON.
    """
    return json.loads(text)


def parse_structured_content_with_fallback(text: str) -> Any:
    """
    Parse text as JSON, falling back to wrapped object on failure.

    Args:
        text: The text content to parse.

    Returns:
        The parsed JSON value if valid, or {"text": text} if parsing fails.
    """
    try:
        return parse_structured_content(text)
    except json.JSONDecodeError:
        return {"text": text}


def inject_structured_content(data: dict) -> None:
    """
    Inject structuredContent into an MCP response's result object.

    This function mutates the input data dictionary in place, adding
    the structuredContent field parsed from the content array's text.

    Args:
        data: The MCP response dictionary to transform. Must have a
              'result' key with a 'content' array.
    """
    result = data.get("result")
    if not isinstance(result, dict):
        return

    content = result.get("content")
    if not isinstance(content, list):
        return

    text = extract_text_content(content)
    if text is None:
        if len(content) == 0:
            result["structuredContent"] = {}
        return

    structured = parse_structured_content_with_fallback(text)
    result["structuredContent"] = structured


def process_response_line(line: str) -> str:
    """
    Process a single response line from the MCP bridge.

    Non-JSON lines are passed through unchanged.
    JSON lines that need transformation are modified to add structuredContent.

    Note: The caller is responsible for flushing the output immediately after
    writing the returned line (e.g., sys.stdout.flush() or print(..., flush=True))
    to ensure unbuffered output per PRD §3.1 FR9.

    Args:
        line: The response line to process.

    Returns:
        The processed line (transformed JSON or original non-JSON), ready
        to be written to stdout with immediate flush.
    """
    if not is_json_line(line):
        return line

    success, data = parse_json_safe(line)
    if not success:
        return line

    if not needs_transformation(data):
        return line

    inject_structured_content(data)
    return json.dumps(data)
