"""Tests for SharedMetricsStore."""

import time

import pytest

from mcpbridge_wrapper.webui.shared_metrics import (
    CLIENT_IDENTITIES_RETENTION_SECONDS,
    SharedMetricsStore,
)


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

    def test_in_flight_tracks_outstanding_requests(self, store):
        """in_flight is non-zero while request is pending and zero after response."""
        store.record_request("BuildProject", request_id="123")
        summary = store.get_summary()
        assert summary["in_flight"] == 1

        store.record_response("BuildProject", request_id="123", error=False, latency_ms=100.0)
        summary = store.get_summary()
        assert summary["in_flight"] == 0

    def test_in_flight_aggregates_across_store_instances(self, tmp_path):
        """Separate processes (store instances) share outstanding in-flight count."""
        db_path = tmp_path / "shared_in_flight.db"
        store_a = SharedMetricsStore(db_path=db_path)
        store_b = SharedMetricsStore(db_path=db_path)
        store_a.reset()

        store_a.record_request("BuildProject", request_id="a1")
        store_b.record_request("OpenFile", request_id="b1")

        summary = store_a.get_summary()
        assert summary["in_flight"] == 2

        store_a.record_response("BuildProject", request_id="a1", error=False, latency_ms=10.0)
        summary = store_b.get_summary()
        assert summary["in_flight"] == 1

        store_b.record_response("OpenFile", request_id="b1", error=False, latency_ms=20.0)
        summary = store_a.get_summary()
        assert summary["in_flight"] == 0

        store_a.close()
        store_b.close()

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


class TestSharedMetricsStoreClientInfo:
    """Tests for client identification in SharedMetricsStore."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary SharedMetricsStore for testing."""
        db_path = tmp_path / "test_metrics.db"
        store = SharedMetricsStore(db_path=db_path)
        store.reset()
        return store

    def test_initial_client_info_unknown(self, store):
        """Test that client info defaults to 'unknown' when not set."""
        summary = store.get_summary()
        assert summary["client_name"] == "unknown"
        assert summary["client_version"] == "unknown"
        assert summary["clients"] == []

    def test_set_client_info(self, store):
        """Test that set_client_info stores and retrieves client identity."""
        store.set_client_info("Cursor", "1.2.3")
        summary = store.get_summary()
        assert summary["client_name"] == "Cursor"
        assert summary["client_version"] == "1.2.3"
        assert len(summary["clients"]) == 1
        assert summary["clients"][0]["name"] == "Cursor"
        assert summary["clients"][0]["version"] == "1.2.3"
        assert summary["clients"][0]["initialize_count"] == 1

    def test_set_client_info_upsert(self, store):
        """Test latest-client overwrite while retaining multi-client history."""
        store.set_client_info("Cursor", "1.0.0")
        store.set_client_info("Claude", "3.5.0")
        summary = store.get_summary()
        assert summary["client_name"] == "Claude"
        assert summary["client_version"] == "3.5.0"
        assert len(summary["clients"]) == 2

    def test_set_client_info_same_client_increments_count(self, store):
        """Repeated initialize from same client increments initialize_count."""
        store.set_client_info("Cursor", "1.0.0")
        store.set_client_info("Cursor", "1.0.0")
        summary = store.get_summary()
        assert len(summary["clients"]) == 1
        assert summary["clients"][0]["initialize_count"] == 2

    def test_set_client_info_prunes_stale_client_identities(self, store):
        """set_client_info removes stale client identities beyond retention."""
        now = time.time()
        stale_time = now - CLIENT_IDENTITIES_RETENTION_SECONDS - 10.0
        fresh_time = now - 5.0

        with store._transaction() as conn:
            conn.execute(
                """INSERT INTO client_identities
                   (client_name, client_version, last_seen, initialize_count)
                   VALUES (?, ?, ?, ?)""",
                ("stale", "0.1", stale_time, 1),
            )
            conn.execute(
                """INSERT INTO client_identities
                   (client_name, client_version, last_seen, initialize_count)
                   VALUES (?, ?, ?, ?)""",
                ("fresh", "1.0", fresh_time, 1),
            )

        store.set_client_info("Cursor", "1.2.3")
        summary = store.get_summary()
        identities = {(client["name"], client["version"]) for client in summary["clients"]}

        assert ("stale", "0.1") not in identities
        assert ("fresh", "1.0") in identities
        assert ("Cursor", "1.2.3") in identities

    def test_reset_clears_client_info(self, store):
        """Test that reset() clears client info back to 'unknown'."""
        store.set_client_info("Cursor", "1.2.3")
        store.reset()
        summary = store.get_summary()
        assert summary["client_name"] == "unknown"
        assert summary["client_version"] == "unknown"
        assert summary["clients"] == []

    def test_error_counts_by_code_empty_by_default(self, store):
        """Test that error_counts_by_code is empty when no errors recorded."""
        summary = store.get_summary()
        assert "error_counts_by_code" in summary
        assert summary["error_counts_by_code"] == {}

    def test_record_response_with_error_code(self, store):
        """Test that error_code is stored and aggregated in get_summary."""
        store.record_request("BuildProject", request_id="1")
        store.record_response(
            "BuildProject",
            request_id="1",
            error=True,
            latency_ms=50.0,
            error_code=-32600,
            error_message="Invalid Request",
        )
        summary = store.get_summary()
        assert summary["error_counts_by_code"] == {-32600: 1}

    def test_record_response_multiple_error_codes(self, store):
        """Test that multiple error codes are aggregated correctly."""
        store.record_request("BuildProject", request_id="1")
        store.record_response(
            "BuildProject", request_id="1", error=True, latency_ms=50.0, error_code=-32600
        )
        store.record_request("OpenFile", request_id="2")
        store.record_response(
            "OpenFile", request_id="2", error=True, latency_ms=30.0, error_code=-32600
        )
        store.record_request("RunTest", request_id="3")
        store.record_response("RunTest", request_id="3", error=True, latency_ms=20.0, error_code=1)
        summary = store.get_summary()
        assert summary["error_counts_by_code"][-32600] == 2
        assert summary["error_counts_by_code"][1] == 1

    def test_record_response_error_without_code(self, store):
        """Test that errors without error_code don't appear in error_counts_by_code."""
        store.record_request("BuildProject", request_id="1")
        store.record_response("BuildProject", request_id="1", error=True, latency_ms=50.0)
        summary = store.get_summary()
        assert summary["error_counts_by_code"] == {}

    def test_record_response_error_code_no_request_id(self, store):
        """Test recording error_code without request_id (insert path)."""
        store.record_response("BuildProject", error=True, latency_ms=50.0, error_code=-32001)
        summary = store.get_summary()
        assert summary["error_counts_by_code"] == {-32001: 1}

    def test_record_param_keys_upserts_count(self, store):
        """record_param_keys increments count on repeated same signature."""
        store.record_param_keys("XcodeGrep", ["pattern", "path"])
        store.record_param_keys("XcodeGrep", ["path", "pattern"])  # sorted same
        patterns = store.get_param_patterns("XcodeGrep")
        assert len(patterns) == 1
        assert patterns[0]["count"] == 2
        assert sorted(patterns[0]["keys"]) == ["path", "pattern"]

    def test_record_param_keys_different_signatures(self, store):
        """Different key combos stored separately."""
        store.record_param_keys("XcodeGrep", ["pattern"])
        store.record_param_keys("XcodeGrep", ["pattern", "path"])
        patterns = store.get_param_patterns("XcodeGrep")
        assert len(patterns) == 2

    def test_get_param_patterns_returns_ranked_list(self, store):
        """get_param_patterns returns patterns sorted by count descending."""
        store.record_param_keys("Tool", ["a"])
        store.record_param_keys("Tool", ["b"])
        store.record_param_keys("Tool", ["b"])
        patterns = store.get_param_patterns("Tool")
        assert patterns[0]["keys"] == ["b"]
        assert patterns[0]["count"] == 2

    def test_get_param_patterns_unknown_tool_empty(self, store):
        """Returns empty list for tool with no recorded patterns."""
        patterns = store.get_param_patterns("NoSuchTool")
        assert patterns == []

    def test_get_param_patterns_top_n(self, store):
        """top_n limits the number of returned patterns."""
        for i in range(5):
            store.record_param_keys("Tool", [f"key{i}"])
        patterns = store.get_param_patterns("Tool", top_n=2)
        assert len(patterns) == 2

    def test_reset_clears_param_patterns(self, store):
        """reset() removes all param_patterns rows."""
        store.record_param_keys("XcodeGrep", ["pattern"])
        store.reset()
        patterns = store.get_param_patterns("XcodeGrep")
        assert patterns == []
