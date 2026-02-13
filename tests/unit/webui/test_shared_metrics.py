"""Tests for SharedMetricsStore."""

import time

import pytest

from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore


class TestSharedMetricsStore:
    """Tests for SharedMetricsStore."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary SharedMetricsStore for testing."""
        db_path = tmp_path / "test_metrics.db"
        store = SharedMetricsStore(db_path=db_path)
        store.reset()
        return store

    def test_record_request(self, store):
        """Test recording a request."""
        store.record_request("BuildProject", request_id="123")
        store.record_response("BuildProject", request_id="123", error=False, latency_ms=100.0)
        summary = store.get_summary()
        assert summary["total_requests"] == 1
        assert summary["tool_counts"]["BuildProject"] == 1

    def test_record_response(self, store):
        """Test recording a response updates latency and error."""
        store.record_request("BuildProject", request_id="123")
        store.record_response("BuildProject", request_id="123", error=False, latency_ms=100.0)
        summary = store.get_summary()
        assert summary["total_requests"] == 1
        assert summary["total_errors"] == 0
        assert "BuildProject" in summary["tool_latency"]
        assert summary["tool_latency"]["BuildProject"]["avg_ms"] == 100.0

    def test_record_error(self, store):
        """Test recording an error response."""
        store.record_request("BuildProject", request_id="123")
        store.record_response("BuildProject", request_id="123", error=True, latency_ms=50.0)
        summary = store.get_summary()
        assert summary["total_errors"] == 1
        assert summary["tool_errors"]["BuildProject"] == 1

    def test_get_timeseries_format(self, store):
        """Test that get_timeseries returns correct format for frontend."""
        # Record some test data
        store.record_request("Tool1", request_id="1")
        store.record_response("Tool1", request_id="1", error=False, latency_ms=100.0)
        store.record_request("Tool2", request_id="2")
        store.record_response("Tool2", request_id="2", error=True, latency_ms=50.0)

        result = store.get_timeseries(seconds=60)

        # Check structure
        assert "requests" in result
        assert "errors" in result
        assert "latencies" in result

        # Check that each is a list
        assert isinstance(result["requests"], list)
        assert isinstance(result["errors"], list)
        assert isinstance(result["latencies"], list)

    def test_get_timeseries_point_format(self, store):
        """Test that timeseries points have correct t/v format."""
        store.record_request("BuildProject", request_id="1")
        store.record_response("BuildProject", request_id="1", error=False, latency_ms=100.0)

        result = store.get_timeseries(seconds=60)

        # Check point format
        for category in ["requests", "errors", "latencies"]:
            for point in result[category]:
                assert "t" in point, f"Missing 't' in {category} point"
                assert "v" in point, f"Missing 'v' in {category} point"
                assert isinstance(point["t"], int), f"'t' should be int in {category}"
                assert isinstance(point["v"], (int, float)), f"'v' should be number in {category}"

    def test_get_timeseries_t_values_are_seconds_ago(self, store):
        """Test that t values are seconds ago (non-negative integers)."""
        store.record_request("BuildProject", request_id="1")
        store.record_response("BuildProject", request_id="1", error=False, latency_ms=100.0)

        result = store.get_timeseries(seconds=60)

        # All t values should be >= 0 and <= 60
        for category in ["requests", "errors"]:
            for point in result[category]:
                assert 0 <= point["t"] <= 60, f"t={point['t']} out of range"

    def test_get_timeseries_buckets_requests(self, store):
        """Test that requests are properly bucketed by time."""
        # Simulate requests at different times by manipulating timestamps
        # We'll insert records and check bucketing
        for i in range(10):
            store.record_request(f"Tool{i}", request_id=str(i))
            store.record_response(
                f"Tool{i}", request_id=str(i), error=False, latency_ms=float(i * 10)
            )

        result = store.get_timeseries(seconds=60)

        # All requests should be in the 0 bucket (same 5-second window)
        total_requests = sum(p["v"] for p in result["requests"])
        assert total_requests == 10

    def test_get_timeseries_error_counting(self, store):
        """Test that errors are counted correctly in timeseries."""
        # 3 successful requests
        for i in range(3):
            store.record_request(f"Tool{i}", request_id=f"ok{i}")
            store.record_response(f"Tool{i}", request_id=f"ok{i}", error=False, latency_ms=100.0)

        # 2 error requests
        for i in range(2):
            store.record_request(f"Tool{i}", request_id=f"err{i}")
            store.record_response(f"Tool{i}", request_id=f"err{i}", error=True, latency_ms=50.0)

        result = store.get_timeseries(seconds=60)

        # Total errors should be 2
        total_errors = sum(p["v"] for p in result["errors"])
        assert total_errors == 2

    def test_uptime_is_dynamic(self, tmp_path):
        """Test that uptime_seconds reflects actual elapsed time, not window_seconds."""
        db_path = tmp_path / "uptime_test.db"
        store = SharedMetricsStore(db_path=db_path)

        summary1 = store.get_summary()
        uptime1 = summary1["uptime_seconds"]
        assert uptime1 >= 0
        # Uptime should NOT equal the default window_seconds (3600)
        assert uptime1 != 3600, "uptime_seconds should not be the query window"

        time.sleep(0.1)

        summary2 = store.get_summary()
        uptime2 = summary2["uptime_seconds"]
        assert uptime2 > uptime1, "uptime_seconds should increase over time"
        store.close()

    def test_uptime_independent_of_window_seconds(self, tmp_path):
        """Test that uptime does not change when window_seconds parameter changes."""
        db_path = tmp_path / "uptime_window_test.db"
        store = SharedMetricsStore(db_path=db_path)

        summary_1h = store.get_summary(window_seconds=3600)
        summary_5m = store.get_summary(window_seconds=300)

        # Uptime should be approximately the same regardless of window_seconds
        assert abs(summary_1h["uptime_seconds"] - summary_5m["uptime_seconds"]) < 1.0
        store.close()

    def test_reset_clears_all_data(self, store):
        """Test that reset clears all metrics data."""
        store.record_request("BuildProject", request_id="1")
        store.record_response("BuildProject", request_id="1", error=False, latency_ms=100.0)

        # Verify data exists
        summary = store.get_summary()
        assert summary["total_requests"] == 1

        # Reset
        store.reset()

        # Verify data is cleared
        summary = store.get_summary()
        assert summary["total_requests"] == 0
        assert summary["total_errors"] == 0
        assert summary["tool_counts"] == {}
