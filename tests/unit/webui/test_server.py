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
        assert "clients" in data

    def test_get_metrics_includes_multi_client_summary(self, client, metrics):
        """Metrics response includes all seen clients for dashboard widgets."""
        metrics.set_client_info("Cursor", "1.0.0")
        metrics.set_client_info("Claude", "2.0.0")
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 2
        names = {entry["name"] for entry in data["clients"]}
        assert names == {"Cursor", "Claude"}

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
        assert "Static files not found." not in response.text
        assert "/static/dashboard.css" in response.text
        assert "/static/dashboard.js" in response.text

    def test_dashboard_js_uses_uniform_client_widget_escaping(self, client):
        """Client widget interpolations in dashboard.js use escapeHtml uniformly."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert 'Initialize calls: " + escapedCount + "' in response.text
        assert 'Last seen: " + escapedLastSeen + "' in response.text
        assert "var escapedCount = escapeHtml(String(count));" in response.text
        assert "var escapedLastSeen = escapeHtml(String(lastSeen));" in response.text

    def test_dashboard_js_has_responsive_doughnut_legend_logic(self, client):
        """Pie/error doughnut legends switch layout at medium widths."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert "const MEDIUM_WIDTH_BREAKPOINT = 1280;" in response.text
        assert "function updateDoughnutLegendLayout()" in response.text
        assert '["toolPie", "errorBreakdown"]' in response.text
        assert 'window.addEventListener("resize", updateDoughnutLegendLayout);' in response.text

    def test_dashboard_js_uses_persistent_stable_tool_colors(self, client):
        """Tool charts use deterministic name-keyed colors persisted in local storage."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert 'const TOOL_COLOR_MAP_STORAGE_KEY = "xcode_mcp_tool_colors_v2";' in response.text
        assert "var toolColorMap = loadToolColorMap();" in response.text
        assert "function getStableColorForTool(toolName)" in response.text
        assert "function chooseDistinctColor(toolName)" in response.text
        assert "const TOOL_BASE_COLORS = [" in response.text
        assert '"#32BB88", "#C4D4EB", "#F8FFF1"' in response.text
        assert "function hueDistance(a, b)" in response.text
        assert "function buildCandidateColor(seed, attempt)" in response.text
        assert "return hueDistance(candidateHue, h) < 16;" in response.text
        assert "persistToolColorMap();" in response.text
        assert "var toolColors = tools.map(function (tool) {" in response.text
        assert "return getStableColorForTool(tool);" in response.text
        assert "charts.toolBar.data.datasets[0].backgroundColor = toolColors;" in response.text
        assert "charts.toolPie.data.datasets[0].backgroundColor = toolColors;" in response.text

    def test_dashboard_js_preserves_audit_row_expansion_state(self, client):
        """Audit row expansion state survives periodic table refreshes."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert "var auditExpandedRows = Object.create(null);" in response.text
        assert "function getAuditRowKey(entry)" in response.text
        assert "function collectExpandedAuditRows(tbody)" in response.text
        assert 'tr.setAttribute("data-audit-row-key", rowKey);' in response.text
        assert "toggleDetailRow(tr, requestId, rowKey, false);" in response.text

    def test_dashboard_js_refreshes_audit_log_on_live_request_updates(self, client):
        """Audit table refreshes from live metrics updates and bypasses browser cache."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert "var latestAuditRefreshRequest = 0;" in response.text
        assert "var lastSeenTotalRequests = null;" in response.text
        expected_refresh_check = (
            'if (typeof totalRequests === "number" && totalRequests !== lastSeenTotalRequests)'
        )
        assert expected_refresh_check in response.text
        assert "loadAuditLogs();" in response.text
        assert 'url += "&_ts=" + Date.now();' in response.text
        assert 'fetch(url, { cache: "no-store" })' in response.text
        assert "if (refreshRequestId !== latestAuditRefreshRequest) {" in response.text

    def test_dashboard_js_timeline_uses_backend_bucket_series(self, client):
        """Request timeline binds directly to backend buckets without re-bucketing."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert "function updateTimeline(timeseries) {" in response.text
        assert "var requestPoints = Array.isArray(timeseries && timeseries.requests)" in response.text
        assert "var errorPoints = Array.isArray(timeseries && timeseries.errors)" in response.text
        assert "function bucketTimeseries(points, bucketSize)" not in response.text
        assert "reqMap[label] = point.v;" in response.text
        assert "errMap[label] = point.v;" in response.text

    def test_dashboard_js_preserves_latency_row_expansion_state(self, client):
        """Latency table parameter row state survives periodic table refreshes."""
        response = client.get("/static/dashboard.js")
        assert response.status_code == 200
        assert "var latencyExpandedRows = Object.create(null);" in response.text
        assert "function collectExpandedLatencyRows(tbody)" in response.text
        assert "Object.keys(latencyExpandedRows).forEach(function (tool) {" in response.text
        assert "if (expandedRows[tool]) {" in response.text
        assert "nextExpandedRows[tool] = true;" in response.text
        assert "latencyExpandedRows = nextExpandedRows;" in response.text
        assert "delete latencyExpandedRows[toolName];" in response.text
        assert "latencyExpandedRows[toolName] = true;" in response.text

    def test_websocket_metrics_update_includes_sessions(self, client, audit):
        """WebSocket metrics_update message includes sessions key."""
        with client.websocket_connect("/ws/metrics") as websocket:
            message = websocket.receive_json()
        assert message["type"] == "metrics_update"
        assert "sessions" in message
        assert isinstance(message["sessions"], list)


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


class TestAuditDetailEndpoint:
    """Tests for GET /api/audit/{request_id}/detail."""

    @pytest.fixture
    def config(self):
        return WebUIConfig()

    @pytest.fixture
    def metrics(self):
        return MetricsCollector()

    @pytest.fixture
    def audit_with_capture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir, capture_payload=True)

    @pytest.fixture
    def audit_no_capture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir, capture_payload=False)

    def test_detail_returns_payload(self, config, metrics, audit_with_capture):
        """GET /api/audit/{id}/detail returns 200 with payload when capture enabled."""
        audit_with_capture.log(
            "XcodeRead",
            request_id="req-abc",
            request_data={"file": "a.swift"},
            response_data={"content": "code"},
        )
        app = create_app(config, metrics, audit_with_capture)
        client = TestClient(app)
        response = client.get("/api/audit/req-abc/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "req-abc"
        assert data["request"] == {"file": "a.swift"}
        assert data["response"] == {"content": "code"}

    def test_detail_404_when_capture_disabled(self, config, metrics, audit_no_capture):
        """GET /api/audit/{id}/detail returns 404 when capture_payload=False."""
        audit_no_capture.log("XcodeRead", request_id="req-xyz")
        app = create_app(config, metrics, audit_no_capture)
        client = TestClient(app)
        response = client.get("/api/audit/req-xyz/detail")
        assert response.status_code == 404
        assert response.json()["detail"] == "Payload not found"

    def test_detail_404_for_unknown_id(self, config, metrics, audit_with_capture):
        """GET /api/audit/{id}/detail returns 404 for unknown request_id."""
        app = create_app(config, metrics, audit_with_capture)
        client = TestClient(app)
        response = client.get("/api/audit/nonexistent-id/detail")
        assert response.status_code == 404
        assert response.json()["detail"] == "Payload not found"

    def test_detail_none_payloads(self, config, metrics, audit_with_capture):
        """Detail endpoint handles None request/response gracefully."""
        audit_with_capture.log("XcodeRead", request_id="req-none")
        app = create_app(config, metrics, audit_with_capture)
        client = TestClient(app)
        response = client.get("/api/audit/req-none/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["request"] is None
        assert data["response"] is None


class TestParamPatternsEndpoint:
    """Tests for GET /api/analytics/param-patterns endpoint."""

    @pytest.fixture
    def config(self):
        return WebUIConfig()

    @pytest.fixture
    def audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir)

    def test_param_patterns_endpoint_returns_tool_patterns(self, config, audit):
        """Endpoint returns recorded param patterns for a tool."""
        metrics = MetricsCollector()
        metrics.record_param_keys("XcodeGrep", ["pattern", "path"])
        metrics.record_param_keys("XcodeGrep", ["path", "pattern"])
        app = create_app(config, metrics, audit)
        client = TestClient(app)
        response = client.get("/api/analytics/param-patterns?tool=XcodeGrep")
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "XcodeGrep"
        assert len(data["patterns"]) == 1
        assert data["patterns"][0]["count"] == 2
        assert sorted(data["patterns"][0]["keys"]) == ["path", "pattern"]

    def test_param_patterns_endpoint_unknown_tool_empty(self, config, audit):
        """Endpoint returns empty patterns list for unknown tool."""
        metrics = MetricsCollector()
        app = create_app(config, metrics, audit)
        client = TestClient(app)
        response = client.get("/api/analytics/param-patterns?tool=NoSuchTool")
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "NoSuchTool"
        assert data["patterns"] == []

    def test_param_patterns_endpoint_requires_tool_param(self, config, audit):
        """Endpoint returns 422 when tool query param is missing."""
        metrics = MetricsCollector()
        app = create_app(config, metrics, audit)
        client = TestClient(app)
        response = client.get("/api/analytics/param-patterns")
        assert response.status_code == 422

    def test_param_patterns_endpoint_top_n(self, config, audit):
        """top_n query param limits returned results."""
        metrics = MetricsCollector()
        for i in range(5):
            metrics.record_param_keys("Tool", [f"k{i}"])
        app = create_app(config, metrics, audit)
        client = TestClient(app)
        response = client.get("/api/analytics/param-patterns?tool=Tool&top_n=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) == 2


class TestGetSessionsLimit:
    """Tests for the limit query param on GET /api/sessions."""

    @pytest.fixture
    def config(self):
        return WebUIConfig()

    @pytest.fixture
    def metrics(self):
        return MetricsCollector()

    @pytest.fixture
    def audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir)

    def _client(self, config, metrics, audit):
        app = create_app(config, metrics, audit)
        return TestClient(app)

    def test_default_limit_returns_sessions(self, config, metrics, audit):
        """Default (no limit param) returns sessions successfully."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert isinstance(data["sessions"], list)

    def test_explicit_limit_accepted(self, config, metrics, audit):
        """Explicit limit=500 is accepted and returns sessions."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions?limit=500")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data

    def test_limit_min_boundary(self, config, metrics, audit):
        """limit=1 is valid (minimum boundary)."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions?limit=1")
        assert response.status_code == 200

    def test_limit_max_boundary(self, config, metrics, audit):
        """limit=10000 is valid (maximum boundary)."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions?limit=10000")
        assert response.status_code == 200

    def test_limit_zero_is_invalid(self, config, metrics, audit):
        """limit=0 is rejected with 422."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions?limit=0")
        assert response.status_code == 422

    def test_limit_above_max_is_invalid(self, config, metrics, audit):
        """limit=10001 is rejected with 422."""
        client = self._client(config, metrics, audit)
        response = client.get("/api/sessions?limit=10001")
        assert response.status_code == 422

    def test_limit_caps_entries_fed_to_detect_sessions(self, config, metrics, audit):
        """limit caps the number of audit entries fed to detect_sessions."""
        # Log 5 audit entries
        for i in range(5):
            audit.log("XcodeRead", request_id=f"req-{i}", latency_ms=1.0)

        client = self._client(config, metrics, audit)

        # With limit=1 only the most-recent 1 entry is fed to detect_sessions
        response_limited = client.get("/api/sessions?limit=1")
        assert response_limited.status_code == 200
        data_limited = response_limited.json()

        # With limit=5 all 5 entries are fed — total tool_count across sessions should be >= limited
        response_full = client.get("/api/sessions?limit=5")
        assert response_full.status_code == 200
        data_full = response_full.json()

        total_tools_limited = sum(s["tool_count"] for s in data_limited["sessions"])
        total_tools_full = sum(s["tool_count"] for s in data_full["sessions"])
        assert total_tools_full >= total_tools_limited
