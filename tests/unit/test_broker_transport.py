"""Modern MCP 2026-07-28 broker transport tests."""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.transport import (
    _SESSION_SHIFT,
    UnixSocketServer,
    _alloc_local_id,
    _get_peer_uid,
)
from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState, ClientSession


def _meta(*, token: Any | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "test-client", "version": "1"},
    }
    if token is not None:
        value["progressToken"] = token
    return value


def _request(request_id: Any, method: str, params: dict[str, Any] | None = None) -> str:
    payload = dict(params or {})
    payload.setdefault("_meta", _meta())
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": payload})


def _config(tmp_path: Path) -> BrokerConfig:
    return BrokerConfig(
        socket_path=tmp_path / "broker.sock",
        pid_file=tmp_path / "broker.pid",
        upstream_cmd=["true"],
        queue_ttl=0,
    )


def _daemon(state: BrokerState = BrokerState.READY) -> MagicMock:
    daemon = MagicMock()
    daemon.state = state
    daemon._upstream = MagicMock()
    daemon._upstream.stdin.write = MagicMock()
    daemon._upstream.stdin.drain = AsyncMock()
    ready = asyncio.Event()
    ready.set()
    daemon.upstream_initialized = ready
    catalog_ready = asyncio.Event()
    catalog_ready.set()
    daemon.tools_catalog_ready = catalog_ready
    daemon._tools_list_cache = None
    return daemon


def _session(session_id: int = 1) -> ClientSession:
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return ClientSession(session_id, 501, time.time(), writer)


def _server(tmp_path: Path, state: BrokerState = BrokerState.READY) -> UnixSocketServer:
    return UnixSocketServer(_config(tmp_path), _daemon(state))


def _last_written(session: ClientSession) -> dict[str, Any]:
    raw = session.writer.write.call_args.args[0].decode().strip()
    return json.loads(raw)


@pytest.mark.asyncio
async def test_discovery_is_local_and_advertises_only_modern_version(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    server._sessions[1] = session

    await server._process_client_line(session, _request("discover", "server/discover"))

    response = _last_written(session)
    assert response["result"]["supportedVersions"] == ["2026-07-28"]
    assert response["result"]["resultType"] == "complete"
    assert response["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]
    server._daemon._upstream.stdin.write.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_initialize_is_rejected(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()

    await server._process_client_line(
        session,
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
    )

    response = _last_written(session)
    assert response["error"]["code"] == -32601
    server._daemon._upstream.stdin.write.assert_not_called()


@pytest.mark.asyncio
async def test_missing_metadata_is_rejected(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()

    await server._process_client_line(
        session,
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}),
    )

    response = _last_written(session)
    assert response["error"]["code"] == -32602


@pytest.mark.asyncio
async def test_unknown_version_is_rejected_with_supported_versions(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    message = json.loads(_request(1, "tools/list"))
    message["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2099-01-01"

    await server._process_client_line(session, json.dumps(message))

    response = _last_written(session)
    assert response["error"]["code"] == -32022
    assert response["error"]["data"]["supportedVersions"] == ["2026-07-28"]


@pytest.mark.asyncio
async def test_modern_request_is_remapped_and_result_is_modernized(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session(2)
    server._sessions[2] = session

    await server._process_client_line(
        session,
        _request("call-1", "tools/call", {"name": "BuildProject"}),
    )

    forwarded = json.loads(server._daemon._upstream.stdin.write.call_args.args[0])
    assert forwarded["id"] >> _SESSION_SHIFT == 2
    assert session.string_id_map["call-1"] == (forwarded["id"] & ((1 << _SESSION_SHIFT) - 1))

    await server.route_upstream_response(
        json.dumps({"jsonrpc": "2.0", "id": forwarded["id"], "result": {"content": []}})
    )
    response = _last_written(session)
    assert response["id"] == "call-1"
    assert response["result"]["resultType"] == "complete"
    assert response["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]


@pytest.mark.asyncio
async def test_cancellation_nested_request_id_is_translated(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    await server._process_client_line(session, _request(7, "tools/call", {"name": "BuildProject"}))
    forwarded = json.loads(server._daemon._upstream.stdin.write.call_args.args[0])
    server._daemon._upstream.stdin.write.reset_mock()

    cancellation = {
        "jsonrpc": "2.0",
        "method": "notifications/cancelled",
        "params": {"requestId": 7, "reason": "user"},
    }
    await server._process_client_line(session, json.dumps(cancellation))

    cancelled = json.loads(server._daemon._upstream.stdin.write.call_args.args[0])
    assert cancelled["params"]["requestId"] == forwarded["id"]


@pytest.mark.asyncio
async def test_progress_is_delivered_only_to_owning_client(tmp_path: Path) -> None:
    server = _server(tmp_path)
    first = _session(1)
    second = _session(2)
    server._sessions.update({1: first, 2: second})
    await server._process_client_line(
        first,
        _request(1, "tools/call", {"name": "A", "_meta": _meta(token="same")}),
    )
    await server._process_client_line(
        second,
        _request(1, "tools/call", {"name": "B", "_meta": _meta(token="same")}),
    )
    first.writer.write.reset_mock()
    second.writer.write.reset_mock()

    await server.route_upstream_response(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/progress",
                "params": {"progressToken": (1 << _SESSION_SHIFT) | 1, "progress": 0.5},
            }
        )
    )

    first.writer.write.assert_called_once()
    second.writer.write.assert_not_called()
    routed = json.loads(first.writer.write.call_args.args[0])
    assert routed["params"]["progressToken"] == "same"


@pytest.mark.asyncio
async def test_subscription_ack_and_filtered_event(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    server._sessions[1] = session
    request = _request(99, "subscriptions/listen", {"notifications": {"toolsListChanged": True}})

    await server._process_client_line(session, request)
    ack = _last_written(session)
    assert ack["method"] == "notifications/subscriptions/acknowledged"
    assert ack["params"]["_meta"]["io.modelcontextprotocol/subscriptionId"] == 99

    session.writer.reset_mock()
    await server.emit_tools_list_changed()
    event = _last_written(session)
    assert event["method"] == "notifications/tools/list_changed"
    assert event["params"]["_meta"]["io.modelcontextprotocol/subscriptionId"] == 99


def test_empty_tools_catalog_is_valid_ready_data(tmp_path: Path) -> None:
    daemon = BrokerDaemon(_config(tmp_path))
    assert daemon._fingerprint_tools_catalog({"tools": []}) is not None


@pytest.mark.asyncio
async def test_upstream_malformed_and_unknown_messages_are_dropped(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    server._sessions[1] = session

    await server.route_upstream_response("not json")
    await server.route_upstream_response("[1, 2, 3]")
    await server.route_upstream_response(json.dumps({"jsonrpc": "2.0", "id": "unexpected"}))
    await server.route_upstream_response(
        json.dumps({"jsonrpc": "2.0", "id": (99 << _SESSION_SHIFT) | 1, "result": {}})
    )

    session.writer.write.assert_not_called()


@pytest.mark.asyncio
async def test_process_client_line_reports_parse_and_state_errors(tmp_path: Path) -> None:
    server = _server(tmp_path, BrokerState.STOPPING)
    session = _session()

    await server._process_client_line(session, "{broken")
    assert _last_written(session)["error"]["code"] == -32700

    session.writer.reset_mock()
    await server._process_client_line(session, "[1, 2]")
    assert _last_written(session)["error"]["code"] == -32700

    session.writer.reset_mock()
    await server._process_client_line(session, _request(1, "tools/list"))
    assert _last_written(session)["error"]["code"] == -32001


@pytest.mark.asyncio
async def test_upstream_unavailable_and_write_failure_clean_aliases(tmp_path: Path) -> None:
    daemon = _daemon()
    daemon._upstream = None
    server = UnixSocketServer(_config(tmp_path), daemon)
    session = _session()

    await server._process_client_line(
        session, _request("request", "tools/call", {"name": "BuildProject"})
    )
    assert _last_written(session)["error"]["code"] == -32001
    assert session.pending == {}
    assert session.id_restore == {}

    daemon = _daemon()
    daemon._upstream.stdin.drain = AsyncMock(side_effect=OSError("pipe closed"))
    server = UnixSocketServer(_config(tmp_path), daemon)
    session = _session()
    await server._process_client_line(session, _request(2, "tools/list"))
    assert _last_written(session)["error"]["code"] == -32001
    assert session.int_id_map == {}


@pytest.mark.asyncio
async def test_tools_list_cache_hit_is_modernized(tmp_path: Path) -> None:
    daemon = _daemon()
    daemon._tools_list_cache = json.dumps(
        {"jsonrpc": "2.0", "id": 0, "result": {"tools": [{"name": "BuildProject"}]}}
    )
    server = UnixSocketServer(_config(tmp_path), daemon)
    session = _session()

    await server._process_client_line(session, _request("cached", "tools/list"))

    response = _last_written(session)
    assert response["id"] == "cached"
    assert response["result"]["cacheScope"] == "private"
    daemon._upstream.stdin.write.assert_not_called()


@pytest.mark.asyncio
async def test_queue_timeout_for_cold_catalog_is_deterministic(tmp_path: Path) -> None:
    daemon = _daemon()
    daemon.tools_catalog_ready = asyncio.Event()
    server = UnixSocketServer(_config(tmp_path), daemon)
    session = _session()

    await server._process_client_line(session, _request(1, "tools/list"))

    response = _last_written(session)
    assert response["error"]["code"] == -32001
    assert "catalog" in response["error"]["message"]


@pytest.mark.asyncio
async def test_stop_drains_pending_requests(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    broker_id = (1 << _SESSION_SHIFT) | 7
    session.pending[broker_id] = asyncio.get_running_loop().create_future()
    server._sessions[1] = session

    await server.stop()

    assert session.pending == {}
    assert _last_written(session)["error"]["code"] == -32001


@pytest.mark.asyncio
async def test_read_loop_skips_empty_lines_and_handles_timeout(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    reader = MagicMock()
    reader.readline = AsyncMock(side_effect=[asyncio.TimeoutError(), b"\n", b""])

    await server._read_client_loop(session, reader)

    server._daemon._upstream.stdin.write.assert_not_called()


@pytest.mark.asyncio
async def test_handle_client_accepts_same_uid_and_cleans_up(tmp_path: Path) -> None:
    server = _server(tmp_path)
    server._stop_event.set()
    writer = _session().writer
    reader = MagicMock()
    reader.readline = AsyncMock(return_value=b"")

    with patch("mcpbridge_wrapper.broker.transport._get_peer_uid", return_value=os.getuid()):
        await server._handle_client(reader, writer)

    assert server.sessions == {}
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_handle_client_rejects_uid_mismatch(tmp_path: Path) -> None:
    server = _server(tmp_path)
    writer = _session().writer
    reader = MagicMock()

    with patch("mcpbridge_wrapper.broker.transport._get_peer_uid", return_value=-1):
        await server._handle_client(reader, writer)

    response = json.loads(writer.write.call_args.args[0].decode())
    assert response["error"]["code"] == -32003


def test_peer_uid_fails_closed_without_socket() -> None:
    writer = MagicMock()
    writer.get_extra_info.return_value = None

    with pytest.raises(OSError, match="No underlying socket"):
        _get_peer_uid(writer)


def test_local_id_allocator_skips_active_aliases() -> None:
    session = _session()
    session._next_local_id = (1 << _SESSION_SHIFT) - 1
    session.id_restore[1] = "active"

    assert _alloc_local_id(session) == 2


@pytest.mark.asyncio
async def test_catalog_and_upstream_readiness_waits_can_resume(tmp_path: Path) -> None:
    daemon = _daemon()
    daemon.tools_catalog_ready = asyncio.Event()
    config = _config(tmp_path)
    config.queue_ttl = 0.1
    server = UnixSocketServer(config, daemon)
    session = _session()

    async def warm_catalog() -> None:
        await asyncio.sleep(0)
        daemon._tools_list_cache = json.dumps({"jsonrpc": "2.0", "id": 0, "result": {"tools": []}})
        daemon.tools_catalog_ready.set()

    asyncio.create_task(warm_catalog())
    await server._process_client_line(session, _request(1, "tools/list"))
    assert _last_written(session)["result"]["tools"] == []

    daemon = _daemon()
    daemon.upstream_initialized = asyncio.Event()
    server = UnixSocketServer(config, daemon)
    session = _session()

    async def warm_upstream() -> None:
        await asyncio.sleep(0)
        daemon.upstream_initialized.set()

    asyncio.create_task(warm_upstream())
    await server._process_client_line(session, _request(2, "ping"))
    daemon._upstream.stdin.write.assert_called_once()


@pytest.mark.asyncio
async def test_subscription_validation_and_cancellation_cleanup(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()

    await server._process_client_line(session, _request(1, "subscriptions/listen"))
    assert _last_written(session)["error"]["code"] == -32602

    session.subscriptions[7] = {"notifications": {"toolsListChanged": True}}
    await server._process_client_line(
        session,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": 7},
            }
        ),
    )
    assert 7 not in session.subscriptions
    await server._forward_cancellation(session, {"params": {"requestId": "unknown"}})
    await server._forward_cancellation(session, {})


@pytest.mark.asyncio
async def test_progress_metadata_and_all_subscription_filters_are_routed(tmp_path: Path) -> None:
    server = _server(tmp_path)
    session = _session()
    server._sessions[1] = session
    await server._process_client_line(
        session,
        _request(1, "tools/call", {"name": "A", "_meta": _meta(token={"same": True})}),
    )
    session.writer.reset_mock()

    await server.route_upstream_response(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "notifications/progress",
                "params": {"_meta": {"progressToken": (1 << _SESSION_SHIFT) | 1}},
            }
        )
    )
    routed = _last_written(session)
    assert routed["params"]["_meta"]["progressToken"] == {"same": True}

    session.writer.reset_mock()
    session.subscriptions.update(
        {
            10: {"notifications": {"promptsListChanged": True}},
            11: {"notifications": {"resourcesListChanged": True}},
        }
    )
    await server.route_upstream_response(
        json.dumps({"jsonrpc": "2.0", "method": "notifications/prompts/list_changed", "params": {}})
    )
    await server.route_upstream_response(
        json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/resources/list_changed", "params": {}}
        )
    )
    assert session.writer.write.call_count == 2


@pytest.mark.asyncio
async def test_metrics_record_success_and_broker_failure(tmp_path: Path) -> None:
    metrics = MagicMock()
    audit = MagicMock()
    daemon = _daemon()
    server = UnixSocketServer(_config(tmp_path), daemon, metrics=metrics, audit=audit)
    session = _session()

    await server._process_client_line(session, _request(1, "tools/call", {"name": "BuildProject"}))
    forwarded = json.loads(daemon._upstream.stdin.write.call_args.args[0])
    await server.route_upstream_response(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": forwarded["id"],
                "result": {"isError": True, "content": [{"type": "text", "text": "failed"}]},
            }
        )
    )
    metrics.record_request.assert_called_once()
    metrics.record_response.assert_called_once()
    assert metrics.record_response.call_args.kwargs["error"] is True
    audit.log.assert_called_once()

    daemon = _daemon()
    daemon._upstream = None
    metrics = MagicMock()
    server = UnixSocketServer(_config(tmp_path), daemon, metrics=metrics)
    session = _session()
    await server._process_client_line(session, _request(2, "tools/call", {"name": "BuildProject"}))
    metrics.record_response.assert_called_once()
    assert metrics.record_response.call_args.kwargs["error_code"] == -32001


@pytest.mark.asyncio
async def test_start_stop_and_write_failures_are_contained(tmp_path: Path) -> None:
    server = _server(tmp_path)
    with patch("asyncio.start_unix_server", new=AsyncMock(return_value=MagicMock())):
        await server.start()
    assert server._server is not None
    await server.stop()

    session = _session()
    session.writer.write.side_effect = OSError("closed")
    await server._write_to_session(session, "{}")


@pytest.mark.asyncio
async def test_handle_client_cleans_up_after_reader_failure(tmp_path: Path) -> None:
    server = _server(tmp_path)
    writer = _session().writer
    reader = MagicMock()
    reader.readline = AsyncMock(side_effect=RuntimeError("reader failed"))

    with patch("mcpbridge_wrapper.broker.transport._get_peer_uid", return_value=os.getuid()):
        await server._handle_client(reader, writer)

    assert server.sessions == {}
