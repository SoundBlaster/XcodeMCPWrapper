"""Tests for webui metrics module."""

from unittest.mock import patch

from mcpbridge_wrapper.webui.metrics import MetricsCollector


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_initial_state(self):
        """Test initial state of metrics collector."""
        metrics = MetricsCollector()
        summary = metrics.get_summary()
        assert summary["total_requests"] == 0
        assert summary["total_errors"] == 0
        assert summary["rps"] == 0.0
        assert summary["error_rate"] == 0.0
        assert summary["in_flight"] == 0
        assert summary["tool_counts"] == {}
        assert summary["tool_errors"] == {}
        assert summary["tool_latency"] == {}

    def test_record_request(self):
        """Test recording a request."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")

        summary = metrics.get_summary()
        assert summary["total_requests"] == 1
        assert summary["tool_counts"]["XcodeRead"] == 1

    def test_record_multiple_requests_same_tool(self):
        """Test recording multiple requests for same tool."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")
        metrics.record_request("XcodeRead")
        metrics.record_request("XcodeRead")

        summary = metrics.get_summary()
        assert summary["total_requests"] == 3
        assert summary["tool_counts"]["XcodeRead"] == 3

    def test_record_requests_different_tools(self):
        """Test recording requests for different tools."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")
        metrics.record_request("XcodeWrite")
        metrics.record_request("BuildProject")

        summary = metrics.get_summary()
        assert summary["total_requests"] == 3
        assert summary["tool_counts"]["XcodeRead"] == 1
        assert summary["tool_counts"]["XcodeWrite"] == 1
        assert summary["tool_counts"]["BuildProject"] == 1

    def test_record_request_with_request_id(self):
        """Test recording a request with request ID for latency tracking."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead", request_id="req-123")

        summary = metrics.get_summary()
        assert summary["in_flight"] == 1

    def test_record_response_with_latency(self):
        """Test recording a response with explicit latency."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")
        metrics.record_response("XcodeRead", latency_ms=50.0)

        summary = metrics.get_summary()
        assert summary["total_requests"] == 1
        assert "XcodeRead" in summary["tool_latency"]
        assert summary["tool_latency"]["XcodeRead"]["count"] == 1
        assert summary["tool_latency"]["XcodeRead"]["avg_ms"] == 50.0

    def test_record_response_computes_latency_from_request(self):
        """Test that response computes latency from matching request."""
        metrics = MetricsCollector()

        with patch("time.time", side_effect=[1000.0, 1000.05]):  # 50ms difference
            metrics.record_request("XcodeRead", request_id="req-123")
            metrics.record_response("XcodeRead", request_id="req-123")

        summary = metrics.get_summary()
        assert "XcodeRead" in summary["tool_latency"]
        # 50ms = 0.05s * 1000
        assert abs(summary["tool_latency"]["XcodeRead"]["avg_ms"] - 50.0) < 0.1

    def test_record_error_response(self):
        """Test recording an error response."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")
        metrics.record_response("XcodeRead", error=True)

        summary = metrics.get_summary()
        assert summary["total_errors"] == 1
        assert summary["tool_errors"]["XcodeRead"] == 1

    def test_record_error_convenience_method(self):
        """Test record_error convenience method."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead")
        metrics.record_error("XcodeRead")

        summary = metrics.get_summary()
        assert summary["total_errors"] == 1

    def test_rps_calculation(self):
        """Test requests per second calculation."""
        metrics = MetricsCollector()

        with patch("time.time", return_value=1000.0):
            metrics.record_request("XcodeRead")
            metrics.record_request("XcodeRead")
            metrics.record_request("XcodeRead")

        with patch("time.time", return_value=1000.0):
            summary = metrics.get_summary()
            # 3 requests in 60 second window = 0.05 rps
            assert summary["rps"] == 0.05

    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        metrics = MetricsCollector()

        metrics.record_request("XcodeRead")
        metrics.record_request("XcodeRead")
        metrics.record_response("XcodeRead", error=True)
        metrics.record_response("XcodeRead", error=False)

        summary = metrics.get_summary()
        # 1 error out of 2 requests = 0.5 error rate
        assert summary["error_rate"] == 0.5

    def test_latency_percentiles(self):
        """Test latency percentile calculations."""
        metrics = MetricsCollector()

        for i in range(100):
            metrics.record_request("XcodeRead")
            metrics.record_response("XcodeRead", latency_ms=float(i))

        summary = metrics.get_summary()
        latency_stats = summary["tool_latency"]["XcodeRead"]

        assert latency_stats["count"] == 100
        assert latency_stats["min_ms"] == 0.0
        assert latency_stats["max_ms"] == 99.0
        assert latency_stats["p50_ms"] == 50.0
        assert latency_stats["p95_ms"] == 95.0
        assert latency_stats["p99_ms"] == 99.0

    def test_get_timeseries(self):
        """Test getting time-series data."""
        metrics = MetricsCollector()

        metrics.record_request("XcodeRead")
        metrics.record_response("XcodeRead", latency_ms=50.0)

        timeseries = metrics.get_timeseries(seconds=300)
        assert timeseries["window_seconds"] == 300
        assert len(timeseries["requests"]) == 1
        assert len(timeseries["latencies"]) == 1

    def test_reset(self):
        """Test resetting metrics."""
        metrics = MetricsCollector()

        metrics.record_request("XcodeRead")
        metrics.record_response("XcodeRead", latency_ms=50.0)

        summary_before = metrics.get_summary()
        assert summary_before["total_requests"] == 1

        metrics.reset()

        summary_after = metrics.get_summary()
        assert summary_after["total_requests"] == 0
        assert summary_after["tool_counts"] == {}
        assert summary_after["tool_latency"] == {}

    def test_thread_safety(self):
        """Test thread safety by recording from multiple threads."""
        import threading

        metrics = MetricsCollector()

        def record_requests():
            for _ in range(100):
                metrics.record_request("XcodeRead")

        threads = [threading.Thread(target=record_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = metrics.get_summary()
        assert summary["total_requests"] == 500


class TestMetricsCollectorClientInfo:
    """Tests for MetricsCollector client identification."""

    def test_initial_client_info_unknown(self):
        """Test that client info defaults to 'unknown' on init."""
        metrics = MetricsCollector()
        summary = metrics.get_summary()
        assert summary["client_name"] == "unknown"
        assert summary["client_version"] == "unknown"

    def test_set_client_info(self):
        """Test setting client info is reflected in summary."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.2.3")
        summary = metrics.get_summary()
        assert summary["client_name"] == "Cursor"
        assert summary["client_version"] == "1.2.3"

    def test_set_client_info_overwrite(self):
        """Test that set_client_info overwrites previous values."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.0.0")
        metrics.set_client_info("Claude", "2.0.0")
        summary = metrics.get_summary()
        assert summary["client_name"] == "Claude"
        assert summary["client_version"] == "2.0.0"

    def test_reset_clears_client_info(self):
        """Test that reset() clears client info back to 'unknown'."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.2.3")
        metrics.reset()
        summary = metrics.get_summary()
        assert summary["client_name"] == "unknown"
        assert summary["client_version"] == "unknown"
