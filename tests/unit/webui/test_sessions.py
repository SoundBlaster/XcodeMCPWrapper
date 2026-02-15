"""Tests for webui sessions module — session detection logic."""

from typing import Optional

from mcpbridge_wrapper.webui.sessions import detect_sessions


def _entry(
    ts: float,
    tool: str = "XcodeRead",
    error: Optional[str] = None,
    req_id: Optional[str] = None,
) -> dict:
    """Build a minimal audit entry dict."""
    e: dict = {
        "timestamp": ts,
        "timestamp_iso": "2026-01-01T00:00:00Z",
        "tool": tool,
        "request_id": req_id or f"req_{int(ts)}",
        "latency_ms": 10.0,
    }
    if error is not None:
        e["error"] = error
    return e


class TestDetectSessionsEmpty:
    """Edge case: empty input."""

    def test_empty_list_returns_empty(self):
        assert detect_sessions([]) == []

    def test_none_gap_uses_default(self):
        # Single entry still works with default gap
        result = detect_sessions([_entry(1000.0)])
        assert len(result) == 1


class TestDetectSessionsSingle:
    """Single-call sessions."""

    def test_single_entry_one_session(self):
        result = detect_sessions([_entry(1000.0)])
        assert len(result) == 1
        s = result[0]
        assert s["id"] == "session_0"
        assert s["tool_count"] == 1
        assert s["error_count"] == 0
        assert len(s["tools"]) == 1
        assert s["start"] == 1000.0
        assert s["end"] == 1000.0

    def test_single_error_entry(self):
        result = detect_sessions([_entry(1000.0, error="timeout")])
        assert result[0]["error_count"] == 1


class TestDetectSessionsGrouping:
    """Multiple entries grouped by gap."""

    def test_two_close_entries_same_session(self):
        entries = [_entry(1000.0), _entry(1200.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert len(result) == 1
        assert result[0]["tool_count"] == 2

    def test_two_entries_exactly_at_gap_boundary(self):
        # gap of exactly 300 should NOT split (condition is strictly greater-than)
        entries = [_entry(1000.0), _entry(1300.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert len(result) == 1

    def test_two_entries_over_gap_splits(self):
        entries = [_entry(1000.0), _entry(1301.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert len(result) == 2
        assert result[0]["tool_count"] == 1
        assert result[1]["tool_count"] == 1

    def test_three_entries_two_sessions(self):
        entries = [_entry(1000.0), _entry(1100.0), _entry(2000.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert len(result) == 2
        assert result[0]["tool_count"] == 2
        assert result[1]["tool_count"] == 1

    def test_session_ids_sequential(self):
        entries = [_entry(1000.0), _entry(2000.0), _entry(3000.0)]
        result = detect_sessions(entries, gap_seconds=100)
        ids = [s["id"] for s in result]
        assert ids == ["session_0", "session_1", "session_2"]

    def test_multiple_sessions_start_end(self):
        entries = [_entry(1000.0), _entry(1050.0), _entry(2000.0), _entry(2100.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert len(result) == 2
        assert result[0]["start"] == 1000.0
        assert result[0]["end"] == 1050.0
        assert result[1]["start"] == 2000.0
        assert result[1]["end"] == 2100.0


class TestDetectSessionsZeroGap:
    """Zero gap puts every call in its own session."""

    def test_zero_gap_each_call_own_session(self):
        entries = [_entry(1000.0), _entry(1001.0), _entry(1002.0)]
        result = detect_sessions(entries, gap_seconds=0)
        assert len(result) == 3
        for i, s in enumerate(result):
            assert s["tool_count"] == 1
            assert s["id"] == f"session_{i}"


class TestDetectSessionsToolFields:
    """Verify tool list fields are forwarded correctly."""

    def test_tool_fields_forwarded(self):
        entry = {
            "timestamp": 1000.0,
            "timestamp_iso": "2026-01-01T00:00:00Z",
            "tool": "XcodeWrite",
            "request_id": "abc123",
            "latency_ms": 42.5,
        }
        result = detect_sessions([entry])
        tool = result[0]["tools"][0]
        assert tool["tool"] == "XcodeWrite"
        assert tool["request_id"] == "abc123"
        assert tool["latency_ms"] == 42.5
        assert tool["timestamp"] == 1000.0
        assert tool["timestamp_iso"] == "2026-01-01T00:00:00Z"
        assert tool["error"] is None

    def test_error_field_forwarded(self):
        entry = _entry(1000.0, error="connection refused")
        result = detect_sessions([entry])
        assert result[0]["tools"][0]["error"] == "connection refused"

    def test_missing_optional_fields_default_gracefully(self):
        entry = {"timestamp": 1000.0}
        result = detect_sessions([entry])
        tool = result[0]["tools"][0]
        assert tool["tool"] == ""
        assert tool["request_id"] is None
        assert tool["latency_ms"] is None
        assert tool["error"] is None


class TestDetectSessionsErrorCount:
    """Error counting within sessions."""

    def test_error_count_correct(self):
        entries = [
            _entry(1000.0, error="err"),
            _entry(1010.0),
            _entry(1020.0, error="err2"),
        ]
        result = detect_sessions(entries, gap_seconds=300)
        assert result[0]["error_count"] == 2

    def test_no_errors_zero_count(self):
        entries = [_entry(1000.0), _entry(1010.0)]
        result = detect_sessions(entries, gap_seconds=300)
        assert result[0]["error_count"] == 0


class TestDetectSessionsLargeGap:
    """Large gap values produce single session."""

    def test_very_large_gap_all_in_one_session(self):
        entries = [_entry(float(i * 3600)) for i in range(10)]
        result = detect_sessions(entries, gap_seconds=86400)
        assert len(result) == 1
        assert result[0]["tool_count"] == 10
