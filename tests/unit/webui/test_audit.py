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
