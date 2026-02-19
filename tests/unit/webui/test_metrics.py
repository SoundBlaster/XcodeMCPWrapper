"""Tests for webui metrics module."""

from unittest.mock import patch

from mcpbridge_wrapper.webui.metrics import MetricsCollector, categorize_error


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
        assert summary["clients"] == []

    def test_set_client_info(self):
        """Test setting client info is reflected in summary."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.2.3")
        summary = metrics.get_summary()
        assert summary["client_name"] == "Cursor"
        assert summary["client_version"] == "1.2.3"
        assert len(summary["clients"]) == 1
        assert summary["clients"][0]["name"] == "Cursor"
        assert summary["clients"][0]["version"] == "1.2.3"
        assert summary["clients"][0]["initialize_count"] == 1

    def test_set_client_info_overwrite(self):
        """Test that latest client remains current while history is preserved."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.0.0")
        metrics.set_client_info("Claude", "2.0.0")
        summary = metrics.get_summary()
        assert summary["client_name"] == "Claude"
        assert summary["client_version"] == "2.0.0"
        assert len(summary["clients"]) == 2

    def test_set_client_info_increments_initialize_count(self):
        """Repeated initialize handshakes for same client increment count."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.2.3")
        metrics.set_client_info("Cursor", "1.2.3")
        summary = metrics.get_summary()
        assert len(summary["clients"]) == 1
        assert summary["clients"][0]["initialize_count"] == 2

    def test_set_client_info_caps_identity_history(self):
        """Client identity history is capped and evicts oldest entries first."""
        metrics = MetricsCollector(max_clients=3)
        with patch("time.time", side_effect=[1.0, 2.0, 3.0, 4.0]):
            metrics.set_client_info("A", "1")
            metrics.set_client_info("B", "1")
            metrics.set_client_info("C", "1")
            metrics.set_client_info("D", "1")

        summary = metrics.get_summary()
        identities = {(client["name"], client["version"]) for client in summary["clients"]}
        assert len(summary["clients"]) == 3
        assert ("A", "1") not in identities
        assert ("B", "1") in identities
        assert ("C", "1") in identities
        assert ("D", "1") in identities

    def test_set_client_info_refresh_prevents_recent_client_eviction(self):
        """Refreshing a client updates last_seen and avoids oldest-first eviction."""
        metrics = MetricsCollector(max_clients=3)
        with patch("time.time", side_effect=[1.0, 2.0, 3.0, 4.0, 5.0]):
            metrics.set_client_info("A", "1")
            metrics.set_client_info("B", "1")
            metrics.set_client_info("C", "1")
            metrics.set_client_info("A", "1")
            metrics.set_client_info("D", "1")

        summary = metrics.get_summary()
        identities = {(client["name"], client["version"]) for client in summary["clients"]}
        assert len(summary["clients"]) == 3
        assert ("A", "1") in identities
        assert ("B", "1") not in identities
        assert ("C", "1") in identities
        assert ("D", "1") in identities

    def test_reset_clears_client_info(self):
        """Test that reset() clears client info back to 'unknown'."""
        metrics = MetricsCollector()
        metrics.set_client_info("Cursor", "1.2.3")
        metrics.reset()
        summary = metrics.get_summary()
        assert summary["client_name"] == "unknown"
        assert summary["client_version"] == "unknown"
        assert summary["clients"] == []

    def test_error_counts_by_code_in_summary(self):
        """Test that error_counts_by_code appears in summary."""
        metrics = MetricsCollector()
        summary = metrics.get_summary()
        assert "error_counts_by_code" in summary
        assert summary["error_counts_by_code"] == {}

    def test_record_response_with_error_code(self):
        """Test that error_code is tracked per code value."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead", request_id="1")
        metrics.record_response(
            "XcodeRead",
            request_id="1",
            error=True,
            error_code=-32600,
            error_message="Invalid Request",
        )
        summary = metrics.get_summary()
        assert summary["error_counts_by_code"] == {-32600: 1}

    def test_record_response_multiple_error_codes(self):
        """Test that multiple different error codes are all tracked."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead", request_id="1")
        metrics.record_response("XcodeRead", request_id="1", error=True, error_code=-32600)
        metrics.record_request("XcodeWrite", request_id="2")
        metrics.record_response("XcodeWrite", request_id="2", error=True, error_code=-32601)
        metrics.record_request("XcodeRead", request_id="3")
        metrics.record_response("XcodeRead", request_id="3", error=True, error_code=-32600)
        summary = metrics.get_summary()
        assert summary["error_counts_by_code"][-32600] == 2
        assert summary["error_counts_by_code"][-32601] == 1

    def test_record_response_error_no_code(self):
        """Test that error without code does not affect error_counts_by_code."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead", request_id="1")
        metrics.record_response("XcodeRead", request_id="1", error=True)
        summary = metrics.get_summary()
        assert summary["error_counts_by_code"] == {}

    def test_reset_clears_error_counts(self):
        """Test that reset() clears error_counts_by_code."""
        metrics = MetricsCollector()
        metrics.record_request("XcodeRead", request_id="1")
        metrics.record_response("XcodeRead", request_id="1", error=True, error_code=-32600)
        metrics.reset()
        summary = metrics.get_summary()
        assert summary["error_counts_by_code"] == {}


class TestParamPatterns:
    """Tests for param pattern recording and retrieval."""

    def test_record_param_keys_basic(self):
        """Recording the same key set twice increments count to 2."""
        metrics = MetricsCollector()
        metrics.record_param_keys("XcodeGrep", ["pattern", "path"])
        metrics.record_param_keys("XcodeGrep", ["path", "pattern"])  # same keys, different order
        patterns = metrics.get_param_patterns("XcodeGrep")
        assert len(patterns) == 1
        assert patterns[0]["count"] == 2
        assert sorted(patterns[0]["keys"]) == ["path", "pattern"]

    def test_record_param_keys_different_signatures(self):
        """Different key combos are tracked separately."""
        metrics = MetricsCollector()
        metrics.record_param_keys("XcodeGrep", ["pattern", "path"])
        metrics.record_param_keys("XcodeGrep", ["pattern", "path", "tabIdentifier"])
        patterns = metrics.get_param_patterns("XcodeGrep")
        assert len(patterns) == 2

    def test_get_param_patterns_sorted_by_count(self):
        """Patterns are returned in descending count order."""
        metrics = MetricsCollector()
        metrics.record_param_keys("Tool", ["a"])
        metrics.record_param_keys("Tool", ["b"])
        metrics.record_param_keys("Tool", ["b"])
        metrics.record_param_keys("Tool", ["b"])
        patterns = metrics.get_param_patterns("Tool")
        assert patterns[0]["keys"] == ["b"]
        assert patterns[0]["count"] == 3
        assert patterns[1]["keys"] == ["a"]
        assert patterns[1]["count"] == 1

    def test_get_param_patterns_top_n(self):
        """top_n parameter limits result count."""
        metrics = MetricsCollector()
        for i in range(5):
            metrics.record_param_keys("Tool", [f"key{i}"])
        patterns = metrics.get_param_patterns("Tool", top_n=3)
        assert len(patterns) == 3

    def test_get_param_patterns_unknown_tool(self):
        """Returns empty list for unknown tool."""
        metrics = MetricsCollector()
        patterns = metrics.get_param_patterns("NoSuchTool")
        assert patterns == []

    def test_reset_clears_param_patterns(self):
        """reset() removes all param pattern data."""
        metrics = MetricsCollector()
        metrics.record_param_keys("XcodeGrep", ["pattern"])
        metrics.reset()
        patterns = metrics.get_param_patterns("XcodeGrep")
        assert patterns == []

    def test_record_param_keys_empty_list(self):
        """Empty param key list is stored as empty signature."""
        metrics = MetricsCollector()
        metrics.record_param_keys("Tool", [])
        patterns = metrics.get_param_patterns("Tool")
        assert len(patterns) == 1
        assert patterns[0]["keys"] == []
        assert patterns[0]["count"] == 1

    def test_record_param_keys_multiple_tools(self):
        """Patterns are isolated per tool."""
        metrics = MetricsCollector()
        metrics.record_param_keys("ToolA", ["x"])
        metrics.record_param_keys("ToolB", ["y"])
        assert metrics.get_param_patterns("ToolA")[0]["keys"] == ["x"]
        assert metrics.get_param_patterns("ToolB")[0]["keys"] == ["y"]


class TestCategorizeError:
    """Tests for the categorize_error helper function."""

    def test_protocol_error_lower_bound(self):
        assert categorize_error(-32699) == "protocol"

    def test_protocol_error_upper_bound(self):
        assert categorize_error(-32600) == "protocol"

    def test_protocol_error_middle(self):
        assert categorize_error(-32650) == "protocol"

    def test_timeout_error(self):
        assert categorize_error(-32001) == "timeout"

    def test_tool_error_small_positive(self):
        assert categorize_error(1) == "tool"

    def test_tool_error_large_positive(self):
        assert categorize_error(9999) == "tool"

    def test_unknown_none(self):
        assert categorize_error(None) == "unknown"

    def test_unknown_negative_not_protocol(self):
        assert categorize_error(-1) == "unknown"

    def test_unknown_zero(self):
        assert categorize_error(0) == "unknown"
