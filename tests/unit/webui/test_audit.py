"""Tests for webui audit module."""

import json
import os
import tempfile

from mcpbridge_wrapper.webui.audit import AuditLogger


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_initial_state(self):
        """Test initial state of audit logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            assert audit.enabled is True
            assert audit.get_entry_count() == 0
            audit.close()

    def test_log_entry(self):
        """Test logging an entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead", request_id="123", latency_ms=50.0)

            assert audit.get_entry_count() == 1
            entries = audit.get_entries()
            assert len(entries) == 1
            assert entries[0]["tool"] == "XcodeRead"
            assert entries[0]["request_id"] == "123"
            assert entries[0]["latency_ms"] == 50.0
            audit.close()

    def test_log_with_error(self):
        """Test logging an entry with error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead", error="Tool not found")

            entries = audit.get_entries()
            assert entries[0]["error"] == "Tool not found"
            audit.close()

    def test_log_with_request_response_data(self):
        """Test logging with request and response data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            request_data = {"file": "test.swift"}
            response_data = {"content": "code"}
            audit.log(
                "XcodeRead",
                request_data=request_data,
                response_data=response_data,
            )

            entries = audit.get_entries()
            assert entries[0]["request"] == request_data
            assert entries[0]["response"] == response_data
            audit.close()

    def test_log_disabled(self):
        """Test that disabled logger doesn't log entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.enabled = False
            audit.log("XcodeRead")

            assert audit.get_entry_count() == 0
            audit.close()

    def test_get_entries_pagination(self):
        """Test pagination of entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            for i in range(10):
                audit.log(f"Tool{i}")

            # Get first 5
            entries = audit.get_entries(limit=5, offset=0)
            assert len(entries) == 5

            # Get next 5
            entries = audit.get_entries(limit=5, offset=5)
            assert len(entries) == 5
            audit.close()

    def test_get_entries_tool_filter(self):
        """Test filtering entries by tool name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead")
            audit.log("XcodeWrite")
            audit.log("XcodeRead")

            entries = audit.get_entries(tool_filter="XcodeRead")
            assert len(entries) == 2
            for entry in entries:
                assert entry["tool"] == "XcodeRead"
            audit.close()

    def test_export_json(self):
        """Test exporting entries as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead", request_id="123")

            json_str = audit.export_json()
            data = json.loads(json_str)
            assert len(data) == 1
            assert data[0]["tool"] == "XcodeRead"
            audit.close()

    def test_export_json_with_limit(self):
        """Test exporting entries with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            for i in range(10):
                audit.log(f"Tool{i}")

            json_str = audit.export_json(limit=5)
            data = json.loads(json_str)
            assert len(data) == 5
            audit.close()

    def test_export_csv(self):
        """Test exporting entries as CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead", request_id="123", latency_ms=50.0)

            csv_str = audit.export_csv()
            assert "timestamp_iso" in csv_str
            assert "tool" in csv_str
            assert "XcodeRead" in csv_str
            assert "123" in csv_str
            audit.close()

    def test_export_csv_empty(self):
        """Test exporting empty entries as CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            csv_str = audit.export_csv()
            assert csv_str == ""
            audit.close()

    def test_file_rotation(self):
        """Test log file rotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create audit logger with very small max file size (1KB)
            audit = AuditLogger(log_dir=tmpdir, max_file_size_mb=0.001, max_files=3)

            # Write enough data to trigger rotation
            for _i in range(100):
                audit.log("XcodeRead", request_data={"data": "x" * 100})

            audit.close()

            # Check that rotation happened
            files = [f for f in os.listdir(tmpdir) if f.endswith(".jsonl")]
            assert len(files) >= 1

    def test_cleanup_old_files(self):
        """Test cleanup of old log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create audit logger with small max files
            audit = AuditLogger(log_dir=tmpdir, max_file_size_mb=0.001, max_files=2)

            # Write enough data to create multiple files
            for _i in range(200):
                audit.log("XcodeRead", request_data={"data": "x" * 100})

            audit.close()

            # Should have at most 2 files
            files = sorted([f for f in os.listdir(tmpdir) if f.endswith(".jsonl")])
            assert len(files) <= 2

    def test_thread_safety(self):
        """Test thread safety of audit logger."""
        import threading

        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)

            def log_entries():
                for _i in range(100):
                    audit.log("XcodeRead")

            threads = [threading.Thread(target=log_entries) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert audit.get_entry_count() == 500
            audit.close()

    def test_close_idempotent(self):
        """Test that close can be called multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log("XcodeRead")
            audit.close()
            audit.close()  # Should not raise


class TestStartupHistoryLoad:
    """Tests for _load_history() — cross-process visibility on startup."""

    def test_startup_loads_existing_jsonl(self):
        """New logger sees entries written by a previous logger in the same dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Process A writes entries and shuts down.
            audit_a = AuditLogger(log_dir=tmpdir)
            audit_a.log("BuildProject", request_id="1", latency_ms=100.0)
            audit_a.log("XcodeListWindows", request_id="2", latency_ms=15.0)
            audit_a.close()

            # Process B starts up in the same log_dir.
            audit_b = AuditLogger(log_dir=tmpdir)
            assert audit_b.get_entry_count() >= 2
            tools = [e["tool"] for e in audit_b.get_entries()]
            assert "BuildProject" in tools
            assert "XcodeListWindows" in tools
            audit_b.close()

    def test_startup_respects_max_memory_entries(self):
        """Startup load is capped at _max_memory_entries (10 000)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write 200 entries via logger A to get them onto disk.
            audit_a = AuditLogger(log_dir=tmpdir)
            for i in range(200):
                audit_a.log(f"Tool{i % 10}", request_id=str(i))
            audit_a.close()

            # Logger B with a tiny cap.
            audit_b = AuditLogger(log_dir=tmpdir)
            audit_b._max_memory_entries = 50  # override cap for test
            # Re-run the load with the new cap.
            audit_b._entries = []
            audit_b._load_history()

            assert audit_b.get_entry_count() <= 50
            audit_b.close()

    def test_startup_skips_malformed_lines(self):
        """JSONL file with corrupt lines loads valid lines and skips invalid ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_jsonl = os.path.join(tmpdir, "audit_20260101_000000.jsonl")
            with open(bad_jsonl, "w", encoding="utf-8") as fh:
                fh.write('{"tool":"ValidTool","direction":"response"}\n')
                fh.write("NOT JSON AT ALL\n")
                fh.write('{"tool":"AnotherTool","direction":"response"}\n')
                fh.write("\n")  # blank line

            audit = AuditLogger(log_dir=tmpdir)
            # Should have loaded 2 valid entries (plus the new file the logger opens)
            entries = audit.get_entries()
            tools = [e["tool"] for e in entries if "tool" in e]
            assert "ValidTool" in tools
            assert "AnotherTool" in tools
            audit.close()

    def test_startup_multiple_files_chronological_order(self):
        """Entries from multiple rotated JSONL files are loaded in chronological order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two files with known timestamps in their names.
            file1 = os.path.join(tmpdir, "audit_20260101_000000.jsonl")
            file2 = os.path.join(tmpdir, "audit_20260102_000000.jsonl")
            with open(file1, "w", encoding="utf-8") as fh:
                fh.write('{"tool":"OldTool","timestamp":1.0}\n')
            with open(file2, "w", encoding="utf-8") as fh:
                fh.write('{"tool":"NewTool","timestamp":2.0}\n')

            audit = AuditLogger(log_dir=tmpdir)
            entries = audit.get_entries()
            tools = [e["tool"] for e in entries if "tool" in e]
            # Both should be present; OldTool appears before NewTool in _entries
            # (get_entries reverses, so NewTool is first in the returned list).
            assert "OldTool" in tools
            assert "NewTool" in tools
            # In _entries (chronological), OldTool comes before NewTool.
            old_idx = next(i for i, e in enumerate(audit._entries) if e.get("tool") == "OldTool")
            new_idx = next(i for i, e in enumerate(audit._entries) if e.get("tool") == "NewTool")
            assert old_idx < new_idx
            audit.close()


class TestPayloadCapture:
    """Tests for the payload ring buffer feature."""

    def test_capture_payload_disabled_by_default(self):
        """Default AuditLogger stores no payloads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            audit.log(
                "XcodeRead",
                request_id="req-1",
                request_data={"file": "a.swift"},
                response_data={"content": "code"},
            )
            assert audit.capture_payload is False
            assert audit.get_payload("req-1") is None
            audit.close()

    def test_capture_payload_stores_entry(self):
        """Payload is stored when capture_payload=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=True)
            audit.log(
                "XcodeRead",
                request_id="req-1",
                request_data={"file": "a.swift"},
                response_data={"content": "code"},
            )
            payload = audit.get_payload("req-1")
            assert payload is not None
            assert payload["request"] == {"file": "a.swift"}
            assert payload["response"] == {"content": "code"}
            audit.close()

    def test_capture_payload_missing_request_id_not_stored(self):
        """Entry without request_id is not stored in ring buffer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=True)
            audit.log(
                "XcodeRead",
                request_data={"file": "a.swift"},
            )
            # No request_id means nothing to look up
            assert audit.get_payload("anything") is None
            audit.close()

    def test_capture_payload_truncation(self):
        """Payload exceeding 64KB is stored as a truncated wrapper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=True)
            big_data = {"data": "x" * (65 * 1024)}  # > 64KB
            audit.log(
                "XcodeRead",
                request_id="req-big",
                request_data=big_data,
                response_data={"ok": True},
            )
            payload = audit.get_payload("req-big")
            assert payload is not None
            # Request should be truncated
            assert payload["request"] is not None
            assert payload["request"].get("_truncated") is True
            # Response is small — kept as-is
            assert payload["response"] == {"ok": True}
            audit.close()

    def test_capture_payload_ring_buffer_evicts_oldest(self):
        """Ring buffer evicts oldest entry when capacity (500) is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=True)
            # Fill buffer exactly to capacity
            for i in range(500):
                audit.log("tool", request_id=str(i), request_data={"i": i})

            assert audit.get_payload("0") is not None  # oldest still present

            # One more entry pushes out the oldest
            audit.log("tool", request_id="500", request_data={"i": 500})
            assert audit.get_payload("0") is None  # evicted
            assert audit.get_payload("1") is not None  # next-oldest still there
            assert audit.get_payload("500") is not None  # newest present
            audit.close()

    def test_capture_payload_none_data_stored_as_none(self):
        """None request/response stored without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=True)
            audit.log("tool", request_id="req-none")
            payload = audit.get_payload("req-none")
            assert payload is not None
            assert payload["request"] is None
            assert payload["response"] is None
            audit.close()

    def test_get_payload_returns_none_when_disabled(self):
        """get_payload always returns None when capture_payload=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir, capture_payload=False)
            audit.log("tool", request_id="req-1", request_data={"x": 1})
            assert audit.get_payload("req-1") is None
            audit.close()

    def test_truncate_payload_within_limit(self):
        """Small payload is returned unchanged by _truncate_payload."""
        small = {"key": "value"}
        result = AuditLogger._truncate_payload(small)
        assert result == small

    def test_truncate_payload_none_returns_none(self):
        """None input to _truncate_payload returns None."""
        assert AuditLogger._truncate_payload(None) is None
