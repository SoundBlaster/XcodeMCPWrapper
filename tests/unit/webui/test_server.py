"""Tests for webui server module."""

import base64
import json
import tempfile

import pytest

# Skip all tests if webui dependencies are not installed
pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from mcpbridge_wrapper.webui.audit import AuditLogger
from mcpbridge_wrapper.webui.config import WebUIConfig
from mcpbridge_wrapper.webui.metrics import MetricsCollector
from mcpbridge_wrapper.webui.server import create_app


class TestCreateApp:
    """Test create_app function."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        return WebUIConfig()

    @pytest.fixture
    def metrics(self):
        """Create a test metrics collector."""
        return MetricsCollector()

    @pytest.fixture
    def audit(self):
        """Create a test audit logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir)

    @pytest.fixture
    def client(self, config, metrics, audit):
        """Create a test client."""
        app = create_app(config, metrics, audit)
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_get_metrics(self, client, metrics):
        """Test getting metrics."""
        metrics.record_request("XcodeRead")
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 1
        assert data["tool_counts"]["XcodeRead"] == 1

    def test_get_timeseries(self, client, metrics):
        """Test getting timeseries data."""
        metrics.record_request("XcodeRead")
        response = client.get("/api/metrics/timeseries?seconds=300")
        assert response.status_code == 200
        data = response.json()
        assert data["window_seconds"] == 300
        assert len(data["requests"]) == 1

    def test_reset_metrics(self, client, metrics):
        """Test resetting metrics."""
        metrics.record_request("XcodeRead")
        response = client.post("/api/metrics/reset")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Verify metrics were reset
        summary = metrics.get_summary()
        assert summary["total_requests"] == 0

    def test_get_audit_logs(self, client, audit):
        """Test getting audit logs."""
        audit.log("XcodeRead", request_id="123")
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["tool"] == "XcodeRead"

    def test_get_audit_logs_with_pagination(self, client, audit):
        """Test audit logs pagination."""
        for i in range(10):
            audit.log(f"Tool{i}")

        response = client.get("/api/audit?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 5

    def test_get_audit_logs_with_filter(self, client, audit):
        """Test audit logs with tool filter."""
        audit.log("XcodeRead")
        audit.log("XcodeWrite")
        audit.log("XcodeRead")

        response = client.get("/api/audit?tool=XcodeRead")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 2
        for entry in data["entries"]:
            assert entry["tool"] == "XcodeRead"

    def test_export_audit_json(self, client, audit):
        """Test exporting audit as JSON."""
        audit.log("XcodeRead")
        response = client.get("/api/audit/export/json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = json.loads(response.text)
        assert len(data) == 1

    def test_export_audit_csv(self, client, audit):
        """Test exporting audit as CSV."""
        audit.log("XcodeRead")
        response = client.get("/api/audit/export/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "XcodeRead" in response.text

    def test_get_config(self, client):
        """Test getting config."""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "host" in data
        assert "port" in data
        # Password should be masked
        assert data["auth"]["password"] == "********"

    def test_dashboard_served(self, client):
        """Test that dashboard is served."""
        response = client.get("/")
        assert response.status_code == 200
        assert "XcodeMCPWrapper Dashboard" in response.text


class TestAuth:
    """Test authentication."""

    @pytest.fixture
    def auth_config(self):
        """Create a test config with auth enabled."""
        config = WebUIConfig()
        config._data["auth"]["enabled"] = True
        config._data["auth"]["username"] = "admin"
        config._data["auth"]["password"] = "secret"
        return config

    @pytest.fixture
    def client_with_auth(self, auth_config):
        """Create a test client with auth."""
        metrics = MetricsCollector()
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLogger(log_dir=tmpdir)
            app = create_app(auth_config, metrics, audit)
            return TestClient(app)

    def test_auth_required(self, client_with_auth):
        """Test that auth is required when enabled."""
        response = client_with_auth.get("/api/metrics")
        assert response.status_code == 401

    def test_auth_with_valid_credentials(self, client_with_auth):
        """Test auth with valid credentials."""
        import base64

        credentials = base64.b64encode(b"admin:secret").decode("utf-8")
        response = client_with_auth.get(
            "/api/metrics", headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 200

    def test_auth_with_invalid_credentials(self, client_with_auth):
        """Test auth with invalid credentials."""
        import base64

        credentials = base64.b64encode(b"admin:wrong").decode("utf-8")
        response = client_with_auth.get(
            "/api/metrics", headers={"Authorization": f"Basic {credentials}"}
        )
        assert response.status_code == 401

    def test_health_no_auth_required(self, client_with_auth):
        """Test that health endpoint doesn't require auth."""
        response = client_with_auth.get("/api/health")
        assert response.status_code == 200

    def test_dashboard_injects_ws_token(self, client_with_auth):
        """Test dashboard injects websocket token when auth is enabled."""
        credentials = base64.b64encode(b"admin:secret").decode("utf-8")
        response = client_with_auth.get("/", headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 200
        assert f'window.__WS_AUTH_TOKEN__ = "{credentials}";' in response.text

    def test_websocket_auth_with_query_token(self, client_with_auth):
        """Test websocket auth via token query parameter."""
        credentials = base64.b64encode(b"admin:secret").decode("utf-8")
        with client_with_auth.websocket_connect(f"/ws/metrics?token={credentials}") as websocket:
            message = websocket.receive_json()
        assert message["type"] == "metrics_update"

    def test_websocket_auth_with_basic_header(self, client_with_auth):
        """Test websocket auth via standard Authorization header."""
        credentials = base64.b64encode(b"admin:secret").decode("utf-8")
        with client_with_auth.websocket_connect(
            "/ws/metrics",
            headers={"Authorization": f"Basic {credentials}"},
        ) as websocket:
            message = websocket.receive_json()
        assert message["type"] == "metrics_update"

    def test_websocket_auth_rejects_missing_credentials(self, client_with_auth):
        """Test websocket is rejected when auth is enabled and credentials are missing."""
        with pytest.raises(WebSocketDisconnect) as exc_info, client_with_auth.websocket_connect(
            "/ws/metrics"
        ):
            pass
        assert exc_info.value.code == 4003
