"""End-to-end integration tests for webui."""

import json
import tempfile

import pytest

# Skip all tests if webui dependencies are not installed
pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")

from fastapi.testclient import TestClient

from mcpbridge_wrapper.webui.audit import AuditLogger
from mcpbridge_wrapper.webui.config import WebUIConfig
from mcpbridge_wrapper.webui.metrics import MetricsCollector
from mcpbridge_wrapper.webui.server import create_app


class TestEndToEnd:
    """End-to-end tests simulating real usage."""

    @pytest.fixture
    def setup(self):
        """Set up test environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = WebUIConfig()
            config._data["audit"]["log_dir"] = tmpdir
            metrics = MetricsCollector()
            audit = AuditLogger(log_dir=tmpdir)
            app = create_app(config, metrics, audit)
            client = TestClient(app)
            yield client, config, metrics, audit
            audit.close()

    def test_full_request_lifecycle(self, setup):
        """Test full request lifecycle with metrics and audit."""
        client, config, metrics, audit = setup

        # Simulate a request
        metrics.record_request("XcodeRead", request_id="req-1")

        # Check metrics
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 1
        assert data["in_flight"] == 1

        # Simulate response
        metrics.record_response("XcodeRead", request_id="req-1", latency_ms=50.0)

        # Log to audit
        audit.log("XcodeRead", request_id="req-1", latency_ms=50.0, direction="response")

        # Check updated metrics
        response = client.get("/api/metrics")
        data = response.json()
        assert data["in_flight"] == 0
        assert "XcodeRead" in data["tool_latency"]

        # Check audit logs
        response = client.get("/api/audit")
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["latency_ms"] == 50.0

    def test_multiple_tools_workflow(self, setup):
        """Test workflow with multiple tools."""
        client, config, metrics, audit = setup

        tools = ["XcodeRead", "XcodeWrite", "BuildProject", "RunAllTests"]

        for i, tool in enumerate(tools):
            metrics.record_request(tool, request_id=f"req-{i}")
            metrics.record_response(tool, request_id=f"req-{i}", latency_ms=10.0 * (i + 1))
            audit.log(tool, request_id=f"req-{i}", latency_ms=10.0 * (i + 1))

        # Check all tools in metrics
        response = client.get("/api/metrics")
        data = response.json()
        assert data["total_requests"] == 4
        for tool in tools:
            assert tool in data["tool_counts"]

        # Check all entries in audit
        response = client.get("/api/audit")
        data = response.json()
        assert data["total"] == 4

    def test_error_handling(self, setup):
        """Test error handling and tracking."""
        client, config, metrics, audit = setup

        # Record successful requests
        for _ in range(3):
            metrics.record_request("XcodeRead")
            metrics.record_response("XcodeRead")

        # Record failed requests
        for _ in range(2):
            metrics.record_request("XcodeRead")
            metrics.record_response("XcodeRead", error=True)
            audit.log("XcodeRead", error="Tool execution failed")

        # Check error rate
        response = client.get("/api/metrics")
        data = response.json()
        assert data["total_requests"] == 5
        assert data["total_errors"] == 2
        assert data["error_rate"] == 0.4

        # Check audit has errors
        response = client.get("/api/audit")
        data = response.json()
        error_entries = [e for e in data["entries"] if e.get("error")]
        assert len(error_entries) == 2

    def test_timeseries_data_accumulation(self, setup):
        """Test timeseries data accumulation."""
        client, config, metrics, audit = setup

        # Record requests over time
        for i in range(10):
            metrics.record_request("XcodeRead")
            metrics.record_response("XcodeRead", latency_ms=float(i * 10))

        # Get timeseries
        response = client.get("/api/metrics/timeseries?seconds=300")
        data = response.json()

        assert len(data["requests"]) == 10
        assert len(data["latencies"]) == 10

    def test_metrics_reset(self, setup):
        """Test metrics reset functionality."""
        client, config, metrics, audit = setup

        # Add some data
        for _ in range(5):
            metrics.record_request("XcodeRead")

        # Verify data exists
        response = client.get("/api/metrics")
        assert response.json()["total_requests"] == 5

        # Reset metrics
        response = client.post("/api/metrics/reset")
        assert response.status_code == 200

        # Verify data is cleared
        response = client.get("/api/metrics")
        data = response.json()
        assert data["total_requests"] == 0
        assert data["tool_counts"] == {}

    def test_audit_export_with_filtering(self, setup):
        """Test audit export with filtering."""
        client, config, metrics, audit = setup

        # Add mixed data
        for i in range(5):
            audit.log("XcodeRead", request_id=f"read-{i}")
        for i in range(3):
            audit.log("XcodeWrite", request_id=f"write-{i}")

        # Export all as JSON
        response = client.get("/api/audit/export/json")
        all_data = json.loads(response.text)
        assert len(all_data) == 8

        # Export all as CSV
        response = client.get("/api/audit/export/csv")
        csv_text = response.text
        assert "XcodeRead" in csv_text
        assert "XcodeWrite" in csv_text

    def test_concurrent_requests_simulation(self, setup):
        """Test simulating concurrent requests."""
        client, config, metrics, audit = setup

        import threading

        def make_requests(tool_name, count):
            for i in range(count):
                metrics.record_request(tool_name, request_id=f"{tool_name}-{i}")

        threads = []
        for tool in ["XcodeRead", "XcodeWrite", "BuildProject"]:
            t = threading.Thread(target=make_requests, args=(tool, 10))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all requests recorded
        response = client.get("/api/metrics")
        data = response.json()
        assert data["total_requests"] == 30
        for tool in ["XcodeRead", "XcodeWrite", "BuildProject"]:
            assert data["tool_counts"][tool] == 10
