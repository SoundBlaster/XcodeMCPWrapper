"""Session detection for MCP tool call audit entries.

Groups audit log entries into sessions based on configurable idle gaps.
A new session begins whenever the gap between consecutive tool calls
exceeds ``gap_seconds``.
"""

from typing import Any, Dict, List


def _entry_timestamp(entry: Dict[str, Any]) -> float:
    """Parse a session entry timestamp for deterministic ordering."""
    try:
        return float(entry.get("timestamp", 0.0))
    except (TypeError, ValueError):
        return 0.0


def detect_sessions(
    entries: List[Dict[str, Any]],
    gap_seconds: float = 300.0,
) -> List[Dict[str, Any]]:
    """Group audit entries into sessions by idle gap.

    A session is a contiguous run of tool calls where no consecutive pair
    is separated by more than ``gap_seconds``. Inputs are normalized to
    ``timestamp`` ascending order before grouping to ensure stable,
    non-negative session boundaries even when callers pass newest-first rows.

    Args:
        entries: List of audit log entry dicts. Each entry must have a
            ``timestamp`` key (float, Unix seconds). Additional keys
            ``request_id``, ``tool``, ``timestamp_iso``, ``latency_ms``,
            and ``error`` are forwarded into the session's tool list.
        gap_seconds: Maximum idle gap (in seconds) allowed within a session.
            A gap strictly greater than this value starts a new session.
            Must be >= 0. A value of 0 puts each call in its own session.

    Returns:
        List of session dicts ordered newest-first by session start time.
        Each dict has:

        .. code-block:: python

            {
                "id": "session_0",          # zero-based index string (newest session)
                "start": 1234567890.0,      # timestamp of first tool call
                "end": 1234567890.5,        # timestamp of last tool call
                "tool_count": 3,
                "error_count": 1,
                "tools": [                  # tool calls, oldest first
                    {
                        "request_id": "abc",
                        "tool": "XcodeRead",
                        "timestamp": 1234567890.0,
                        "timestamp_iso": "2026-02-15T00:00:00Z",
                        "latency_ms": 42.5,
                        "error": None,
                    }
                ],
            }
    """
    if not entries:
        return []

    ordered_entries = sorted(entries, key=_entry_timestamp)

    sessions: List[Dict[str, Any]] = []
    current_tools: List[Dict[str, Any]] = []
    prev_ts: float = 0.0

    for entry in ordered_entries:
        ts = _entry_timestamp(entry)

        # Start a new session if this is not the first entry and the gap is too large.
        if current_tools and (ts - prev_ts) > gap_seconds:
            sessions.append(_build_session(len(sessions), current_tools))
            current_tools = []

        current_tools.append(_extract_tool(entry))
        prev_ts = ts

    # Flush the last session.
    if current_tools:
        sessions.append(_build_session(len(sessions), current_tools))

    return _newest_first_sessions(sessions)


def _extract_tool(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant fields from an audit entry for the session tool list."""
    return {
        "request_id": entry.get("request_id"),
        "tool": entry.get("tool", ""),
        "timestamp": _entry_timestamp(entry),
        "timestamp_iso": entry.get("timestamp_iso", ""),
        "latency_ms": entry.get("latency_ms"),
        "error": entry.get("error"),
    }


def _build_session(index: int, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Construct a session dict from a list of tool call dicts."""
    error_count = sum(1 for t in tools if t.get("error") is not None)
    return {
        "id": f"session_{index}",
        "start": tools[0]["timestamp"],
        "end": tools[-1]["timestamp"],
        "tool_count": len(tools),
        "error_count": error_count,
        "tools": tools,
    }


def _newest_first_sessions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return sessions in newest-first order with deterministic IDs."""
    newest_first = list(reversed(sessions))
    for index, session in enumerate(newest_first):
        session["id"] = f"session_{index}"
    return newest_first
