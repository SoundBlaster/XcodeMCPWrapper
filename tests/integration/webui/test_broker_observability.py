"""Integration coverage for broker-hosted Web UI observability."""

from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

import pytest
import pytest_asyncio

# Skip all tests if webui dependencies are not installed
pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")

from fastapi.testclient import TestClient

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.transport import UnixSocketServer
from mcpbridge_wrapper.broker.types import BrokerConfig
from mcpbridge_wrapper.webui.audit import AuditLogger
from mcpbridge_wrapper.webui.config import WebUIConfig
from mcpbridge_wrapper.webui.server import create_app
from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore


@pytest.fixture
def telemetry_upstream_script(tmp_path: Path) -> Path:
    """Create an upstream script that returns both success and error responses."""
    script = tmp_path / "upstream_telemetry.py"
    script.write_text(
        "import json\n"
        "import sys\n"
        "for raw in sys.stdin:\n"
        "    line = raw.strip()\n"
        "    if not line:\n"
        "        continue\n"
        "    msg = json.loads(line)\n"
        "    request_id = msg.get('id')\n"
        "    if request_id is None:\n"
        "        continue\n"
        "    params = msg.get('params', {}) if isinstance(msg.get('params'), dict) else {}\n"
        "    tool_name = params.get('name')\n"
        "    if tool_name == 'FailTool':\n"
        "        response = {\n"
        "            'jsonrpc': '2.0',\n"
        "            'id': request_id,\n"
        "            'error': {'code': -32603, 'message': 'Synthetic upstream failure'},\n"
        "        }\n"
        "    else:\n"
        "        response = {\n"
        "            'jsonrpc': '2.0',\n"
        "            'id': request_id,\n"
        "            'result': {\n"
        "                'content': [{'type': 'text', 'text': 'ok'}],\n"
        "                'tool': tool_name,\n"
        "            },\n"
        "        }\n"
        "    print(json.dumps(response, separators=(',', ':')), flush=True)\n",
        encoding="utf-8",
    )
    return script


@pytest.fixture
def broker_observability_runtime(
    telemetry_upstream_script: Path,
) -> Iterator[dict[str, Any]]:
    """Prepare broker/webui runtime resources with short, deterministic paths."""
    short_dir = Path(tempfile.mkdtemp(dir="/tmp", prefix="mcpbw"))
    try:
        db_path = short_dir / "metrics.db"
        audit_dir = short_dir / "audit"
        yield {
            "short_dir": short_dir,
            "db_path": db_path,
            "audit_dir": audit_dir,
            "broker_config": BrokerConfig(
                socket_path=short_dir / "broker.sock",
                pid_file=short_dir / "broker.pid",
                upstream_cmd=[sys.executable, "-u", str(telemetry_upstream_script)],
                reconnect_backoff_cap=1,
                queue_ttl=2,
                graceful_shutdown_timeout=1,
            ),
        }
    finally:
        shutil.rmtree(short_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def running_broker_with_webui(
    broker_observability_runtime: dict[str, Any],
) -> AsyncIterator[dict[str, Any]]:
    """Start broker transport with shared metrics/audit and a TestClient app."""
    metrics = SharedMetricsStore(db_path=broker_observability_runtime["db_path"])
    audit = AuditLogger(log_dir=str(broker_observability_runtime["audit_dir"]))
    config = WebUIConfig()
    config._data["audit"]["log_dir"] = str(broker_observability_runtime["audit_dir"])

    app = create_app(config, metrics, audit)
    client = TestClient(app)

    broker_config: BrokerConfig = broker_observability_runtime["broker_config"]
    daemon = BrokerDaemon(broker_config)
    transport = UnixSocketServer(broker_config, daemon, metrics=metrics, audit=audit)
    daemon._transport = transport  # noqa: SLF001
    await daemon.start()

    try:
        yield {
            "daemon": daemon,
            "transport": transport,
            "broker_config": broker_config,
            "client": client,
            "metrics": metrics,
            "audit": audit,
        }
    finally:
        with contextlib.suppress(Exception):
            await daemon.stop()
        client.close()
        audit.close()
        metrics.close()


async def _send_client_tool_call(
    broker_config: BrokerConfig,
    *,
    request_id: str,
    client_name: str,
    tool_name: str,
) -> dict[str, Any]:
    """Send initialize + tools/call from one broker client and return tool response."""
    reader, writer = await asyncio.open_unix_connection(str(broker_config.socket_path))
    try:
        initialize = {
            "jsonrpc": "2.0",
            "id": f"init-{request_id}",
            "method": "initialize",
            "params": {"clientInfo": {"name": client_name, "version": "1.0.0"}},
        }
        tool_call = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": {"request_id": request_id}},
        }
        writer.write((json.dumps(initialize, separators=(",", ":")) + "\n").encode())
        writer.write((json.dumps(tool_call, separators=(",", ":")) + "\n").encode())
        await writer.drain()

        tool_response: dict[str, Any] | None = None
        for _ in range(2):
            raw = await asyncio.wait_for(reader.readline(), timeout=2.0)
            assert raw, "Expected broker response line"
            decoded = json.loads(raw.decode())
            if decoded.get("id") == request_id:
                tool_response = decoded

        assert tool_response is not None, f"Missing tool response for {request_id}"
        return tool_response
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


@pytest.mark.asyncio
async def test_broker_telemetry_visible_in_webui_api_under_multi_client_load(
    running_broker_with_webui: dict[str, Any],
) -> None:
    """Broker-routed multi-client traffic is aggregated in metrics/audit API views."""
    broker_config: BrokerConfig = running_broker_with_webui["broker_config"]
    client: TestClient = running_broker_with_webui["client"]

    success_calls = 8
    calls = [
        _send_client_tool_call(
            broker_config,
            request_id=f"ok-{index}",
            client_name=f"Client-{index % 3}",
            tool_name="BuildProject",
        )
        for index in range(success_calls)
    ]
    calls.append(
        _send_client_tool_call(
            broker_config,
            request_id="err-0",
            client_name="Client-error",
            tool_name="FailTool",
        )
    )

    responses = await asyncio.gather(*calls)
    assert sum(1 for response in responses if "result" in response) == success_calls
    error_responses = [response for response in responses if "error" in response]
    assert len(error_responses) == 1
    assert error_responses[0]["error"]["code"] == -32603

    metrics_response = client.get("/api/metrics")
    assert metrics_response.status_code == 200
    metrics_data = metrics_response.json()

    assert metrics_data["total_requests"] == 9
    assert metrics_data["total_errors"] == 1
    assert metrics_data["tool_counts"]["BuildProject"] == success_calls
    assert metrics_data["tool_counts"]["FailTool"] == 1
    assert metrics_data["tool_errors"]["FailTool"] == 1
    error_breakdown = metrics_data["error_counts_by_code"]
    assert error_breakdown.get("-32603", 0) == 1

    client_names = {entry["name"] for entry in metrics_data["clients"]}
    assert "Client-0" in client_names
    assert "Client-1" in client_names

    audit_response = client.get("/api/audit?limit=100")
    assert audit_response.status_code == 200
    audit_data = audit_response.json()
    assert audit_data["total"] >= 9
    entries = audit_data["entries"]
    assert any(entry.get("tool") == "BuildProject" for entry in entries)

    failing_entries = [entry for entry in entries if entry.get("tool") == "FailTool"]
    assert failing_entries, "Expected at least one failing audit entry"
    assert any(entry.get("error_code") == -32603 for entry in failing_entries)
    assert any("Synthetic upstream failure" in str(entry.get("error")) for entry in failing_entries)
