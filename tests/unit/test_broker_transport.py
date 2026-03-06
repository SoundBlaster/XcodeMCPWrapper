"""Tests for UnixSocketServer — P13-T3 implementation.

Covers:
- Server instantiation and basic properties
- route_upstream_response: notification broadcast
- route_upstream_response: targeted response routing + ID restoration
- route_upstream_response: unknown client_id dropped silently
- route_upstream_response: malformed line silently ignored
- Client request processing: ID remapping (int and string IDs)
- Client request processing: malformed payload returns parse error
- Client request processing: upstream unavailable returns -32001
- Two concurrent clients receive independent responses
- Graceful stop drains pending requests with -32001
- Queue TTL during RECONNECTING state
- FU-P13-T12: Peer credential verification (UID enforcement)
- FU-P13-T12: Socket file created with 0600 permissions
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import stat
import struct
import tempfile
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpbridge_wrapper.broker import transport as transport_module
from mcpbridge_wrapper.broker.transport import (
    _ID_MASK,
    _SESSION_SHIFT,
    UnixSocketServer,
    _alloc_local_id,
    _get_peer_uid,
)
from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState, ClientSession

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Any) -> BrokerConfig:
    from pathlib import Path

    base = Path(tmp_path)
    return BrokerConfig(
        socket_path=base / "broker.sock",
        pid_file=base / "broker.pid",
        upstream_cmd=["true"],
        reconnect_backoff_cap=1,
        queue_ttl=2,
        graceful_shutdown_timeout=1,
    )


def _make_daemon_mock(state: BrokerState = BrokerState.READY) -> MagicMock:
    daemon = MagicMock()
    daemon.state = state
    upstream = MagicMock()
    upstream.stdin = MagicMock()
    upstream.stdin.write = MagicMock()
    upstream.stdin.drain = AsyncMock()
    daemon._upstream = upstream
    # Set readiness gate as a pre-set event (upstream already initialized).
    import asyncio as _asyncio

    ready_event = _asyncio.Event()
    ready_event.set()
    daemon.upstream_initialized = ready_event
    # No cached tools/list by default.
    daemon._tools_list_cache = None
    return daemon


def _make_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    writer.get_extra_info = MagicMock(return_value=None)
    return writer


def _make_session(session_id: int = 1) -> ClientSession:
    return ClientSession(
        session_id=session_id,
        peer_uid=501,
        connected_at=time.time(),
        writer=_make_writer(),
    )


def _make_server(tmp_path: Any, state: BrokerState = BrokerState.READY) -> UnixSocketServer:
    cfg = _make_config(tmp_path)
    daemon = _make_daemon_mock(state)
    return UnixSocketServer(cfg, daemon)


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


class TestUnixSocketServerInstantiation:
    @pytest.mark.asyncio
    async def test_sessions_initially_empty(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        assert server.sessions == {}

    @pytest.mark.asyncio
    async def test_next_session_id_starts_at_one(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        assert server._next_session_id == 1


# ---------------------------------------------------------------------------
# route_upstream_response — notifications (broadcast)
# ---------------------------------------------------------------------------


class TestRouteUpstreamNotification:
    @pytest.mark.asyncio
    async def test_notification_broadcast_to_all_clients(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        s2 = _make_session(2)
        server._sessions[1] = s1
        server._sessions[2] = s2

        notification = json.dumps({"jsonrpc": "2.0", "method": "notify", "id": None})
        await server.route_upstream_response(notification)

        s1.writer.write.assert_called()
        s2.writer.write.assert_called()

    @pytest.mark.asyncio
    async def test_notification_without_id_field_is_broadcast(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        server._sessions[1] = s1

        # Message with no "id" field at all
        notification = json.dumps({"jsonrpc": "2.0", "method": "progress", "params": {}})
        # This has no "id" key → msg.get("id") returns None → broadcast
        await server.route_upstream_response(notification)

        s1.writer.write.assert_called()

    @pytest.mark.asyncio
    async def test_malformed_json_is_silently_dropped(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        server._sessions[1] = s1

        await server.route_upstream_response("not json at all {{{")
        # No writes should have been made
        s1.writer.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_object_json_is_silently_dropped(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        server._sessions[1] = s1

        await server.route_upstream_response("[1, 2, 3]")
        s1.writer.write.assert_not_called()


# ---------------------------------------------------------------------------
# route_upstream_response — targeted responses
# ---------------------------------------------------------------------------


class TestRouteUpstreamTargetedResponse:
    @pytest.mark.asyncio
    async def test_integer_id_routed_to_correct_session(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session_id = 3
        original_id = 42
        broker_id = (session_id << _SESSION_SHIFT) | (original_id & _ID_MASK)

        s = _make_session(session_id)
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        s.pending[broker_id] = fut
        server._sessions[session_id] = s

        response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {"ok": True}})
        await server.route_upstream_response(response)

        # Writer should have been called with the restored original ID
        call_arg = s.writer.write.call_args[0][0]
        decoded = json.loads(call_arg.rstrip(b"\n"))
        assert decoded["id"] == original_id

        # Future should be resolved
        assert fut.done()
        assert json.loads(fut.result())["id"] == original_id

    @pytest.mark.asyncio
    async def test_string_id_restored_from_map(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session_id = 1
        s = _make_session(session_id)
        # Simulate that "req-abc" was mapped to int alias 5
        s.string_id_map["req-abc"] = 5
        s.id_restore[5] = "req-abc"
        broker_id = (session_id << _SESSION_SHIFT) | 5
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        s.pending[broker_id] = fut
        server._sessions[session_id] = s

        response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        await server.route_upstream_response(response)

        call_arg = s.writer.write.call_args[0][0]
        decoded = json.loads(call_arg.rstrip(b"\n"))
        assert decoded["id"] == "req-abc"

    @pytest.mark.asyncio
    async def test_unknown_client_id_drops_silently(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        # client_id 99 has no session
        broker_id = (99 << _SESSION_SHIFT) | 1
        response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        # Should not raise
        await server.route_upstream_response(response)

    @pytest.mark.asyncio
    async def test_non_integer_broker_id_dropped(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        server._sessions[1] = s1
        # String id from upstream (unexpected)
        response = json.dumps({"jsonrpc": "2.0", "id": "unexpected-str", "result": {}})
        await server.route_upstream_response(response)
        s1.writer.write.assert_not_called()


# ---------------------------------------------------------------------------
# _process_client_line — request ID remapping
# ---------------------------------------------------------------------------


class TestProcessClientLine:
    @pytest.mark.asyncio
    async def test_integer_id_is_remapped(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(2)
        server._sessions[2] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Verify a local alias was allocated for the integer ID
        assert 10 in session.int_id_map
        local_alias = session.int_id_map[10]
        expected_broker_id = (2 << _SESSION_SHIFT) | local_alias
        assert expected_broker_id in session.pending

        call_bytes: bytes = server._daemon._upstream.stdin.write.call_args[0][0]
        sent = json.loads(call_bytes.rstrip(b"\n"))
        assert sent["id"] == expected_broker_id

    @pytest.mark.asyncio
    async def test_string_id_is_aliased(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": "call-1", "method": "tools/call"})
        await server._process_client_line(session, request)

        assert "call-1" in session.string_id_map
        alias = session.string_id_map["call-1"]
        expected_broker_id = (1 << _SESSION_SHIFT) | alias
        assert expected_broker_id in session.pending

    @pytest.mark.asyncio
    async def test_malformed_json_sends_parse_error(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        await server._process_client_line(session, "{broken json")

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_upstream_unavailable_returns_32001(self, tmp_path: Any) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        daemon._upstream = None
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        await server._process_client_line(session, request)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001

    @pytest.mark.asyncio
    async def test_upstream_unavailable_records_tool_failure_metrics(self, tmp_path: Any) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        daemon._upstream = None
        metrics = MagicMock()
        audit = MagicMock()
        server = UnixSocketServer(cfg, daemon, metrics=metrics, audit=audit)
        session = _make_session(1)
        server._sessions[1] = session

        with patch("mcpbridge_wrapper.broker.transport.time.time", side_effect=[1000.0, 1000.2]):
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "BuildProject"},
                }
            )
            await server._process_client_line(session, request)

        metrics.record_request.assert_called_once()
        metrics.record_response.assert_called_once()
        response_call = metrics.record_response.call_args
        assert response_call.args[0] == "BuildProject"
        assert response_call.kwargs["error"] is True
        assert response_call.kwargs["error_code"] == -32001
        assert response_call.kwargs["error_message"] == "Upstream bridge not available"
        assert response_call.kwargs["latency_ms"] == pytest.approx(200.0)
        audit.log.assert_called_once()

    @pytest.mark.asyncio
    async def test_notification_forwarded_without_pending(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        # Notification has no id field
        request = json.dumps({"jsonrpc": "2.0", "method": "cancelled"})
        await server._process_client_line(session, request)

        assert session.pending == {}
        # Was written to upstream
        server._daemon._upstream.stdin.write.assert_called()


# ---------------------------------------------------------------------------
# Two concurrent clients
# ---------------------------------------------------------------------------


class TestConcurrentClients:
    @pytest.mark.asyncio
    async def test_two_clients_receive_independent_responses(self, tmp_path: Any) -> None:
        """Responses for two concurrent clients are routed independently."""
        server = _make_server(tmp_path)
        s1 = _make_session(1)
        s2 = _make_session(2)
        server._sessions[1] = s1
        server._sessions[2] = s2

        # Simulate s1 pending request with broker_id for session 1, original_id=1
        broker_id_1 = (1 << _SESSION_SHIFT) | 1
        loop = asyncio.get_event_loop()
        fut1: asyncio.Future[str] = loop.create_future()
        s1.pending[broker_id_1] = fut1

        # Simulate s2 pending request with broker_id for session 2, original_id=1
        broker_id_2 = (2 << _SESSION_SHIFT) | 1
        fut2: asyncio.Future[str] = loop.create_future()
        s2.pending[broker_id_2] = fut2

        # Route response for s1
        resp1 = json.dumps({"jsonrpc": "2.0", "id": broker_id_1, "result": {"for": "s1"}})
        await server.route_upstream_response(resp1)

        # Route response for s2
        resp2 = json.dumps({"jsonrpc": "2.0", "id": broker_id_2, "result": {"for": "s2"}})
        await server.route_upstream_response(resp2)

        # s1's response went only to s1
        assert fut1.done()
        result1 = json.loads(fut1.result())
        assert result1["result"]["for"] == "s1"
        assert result1["id"] == 1  # original restored

        # s2's response went only to s2
        assert fut2.done()
        result2 = json.loads(fut2.result())
        assert result2["result"]["for"] == "s2"
        assert result2["id"] == 1  # original restored

        # Each writer called exactly once for targeted response
        s1.writer.write.assert_called_once()
        s2.writer.write.assert_called_once()


# ---------------------------------------------------------------------------
# Graceful stop — drain pending
# ---------------------------------------------------------------------------


class TestGracefulStop:
    @pytest.mark.asyncio
    async def test_stop_sends_32001_for_pending_requests(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        broker_id = (1 << _SESSION_SHIFT) | 7
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        session.pending[broker_id] = fut

        # Patch asyncio.start_unix_server to avoid actual socket creation
        with patch("asyncio.start_unix_server", new=AsyncMock(return_value=MagicMock())):
            await server.start()

        await server.stop()

        # pending should be cleared
        assert session.pending == {}
        # Writer should have been called with a -32001 error
        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001


# ---------------------------------------------------------------------------
# Queue TTL during RECONNECTING
# ---------------------------------------------------------------------------


class TestQueueTTL:
    @pytest.mark.asyncio
    async def test_ttl_exceeded_returns_32001(self, tmp_path: Any) -> None:
        """When upstream_initialized is not set and TTL=0, returns -32001 immediately."""
        cfg = _make_config(tmp_path)
        cfg = BrokerConfig(
            socket_path=cfg.socket_path,
            pid_file=cfg.pid_file,
            upstream_cmd=["true"],
            reconnect_backoff_cap=1,
            queue_ttl=0,  # immediate expiry
            graceful_shutdown_timeout=1,
        )
        daemon = _make_daemon_mock(state=BrokerState.RECONNECTING)
        # Simulate upstream not yet initialized (Xcode approval pending).
        import asyncio as _asyncio

        not_ready = _asyncio.Event()  # NOT set
        daemon.upstream_initialized = not_ready
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        await server._process_client_line(session, request)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001
        assert "TTL" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_upstream_ready_proceeds(self, tmp_path: Any) -> None:
        """When upstream_initialized becomes set, request is forwarded to upstream."""
        import asyncio as _asyncio

        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock(state=BrokerState.READY)
        # Start with upstream not ready; set it after a brief delay.
        ready_event = _asyncio.Event()
        daemon.upstream_initialized = ready_event
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        async def _set_event() -> None:
            await _asyncio.sleep(0.01)
            ready_event.set()

        # Set event slightly after _process_client_line starts waiting.
        _asyncio.ensure_future(_set_event())

        request = json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Request should have been forwarded to upstream
        daemon._upstream.stdin.write.assert_called()


# ---------------------------------------------------------------------------
# _handle_client — session registration and cleanup
# ---------------------------------------------------------------------------


class TestHandleClient:
    @pytest.mark.asyncio
    async def test_session_registered_and_removed(self, tmp_path: Any) -> None:
        """_handle_client registers a session during the read loop and removes it after."""
        server = _make_server(tmp_path)

        writer = _make_writer()
        # Set stop event so the read loop exits immediately
        server._stop_event.set()

        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b"")

        await server._handle_client(reader, writer)

        # Session should be removed after disconnect
        assert server._sessions == {}

    @pytest.mark.asyncio
    async def test_peer_uid_from_tuple(self, tmp_path: Any) -> None:
        """_handle_client handles tuple peername correctly."""
        server = _make_server(tmp_path)
        server._stop_event.set()

        writer = _make_writer()
        writer.get_extra_info = MagicMock(return_value=("/tmp/sock", 501))

        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b"")

        await server._handle_client(reader, writer)
        # Should not raise; session cleaned up
        assert server._sessions == {}

    @pytest.mark.asyncio
    async def test_exception_in_read_loop_is_handled(self, tmp_path: Any) -> None:
        """_handle_client logs and cleans up when the read loop raises."""
        server = _make_server(tmp_path)

        writer = _make_writer()
        reader = MagicMock()
        reader.readline = AsyncMock(side_effect=RuntimeError("boom"))

        await server._handle_client(reader, writer)
        assert server._sessions == {}


# ---------------------------------------------------------------------------
# _read_client_loop — branches
# ---------------------------------------------------------------------------


class TestReadClientLoop:
    @pytest.mark.asyncio
    async def test_empty_line_is_skipped(self, tmp_path: Any) -> None:
        """_read_client_loop skips empty decoded lines."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        reader = MagicMock()
        # Return empty string line, then b"" to signal disconnect
        reader.readline = AsyncMock(side_effect=[b"\n", b""])
        await server._read_client_loop(session, reader)

        # No upstream writes triggered (line was empty)
        server._daemon._upstream.stdin.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_read_exception_breaks_loop(self, tmp_path: Any) -> None:
        """_read_client_loop breaks on unexpected read exception."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        reader = MagicMock()
        reader.readline = AsyncMock(side_effect=OSError("connection reset"))
        await server._read_client_loop(session, reader)
        # Should complete without raising

    @pytest.mark.asyncio
    async def test_timeout_then_disconnect(self, tmp_path: Any) -> None:
        """_read_client_loop retries on TimeoutError then exits on EOF."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        reader = MagicMock()
        reader.readline = AsyncMock(side_effect=[asyncio.TimeoutError(), b""])
        await server._read_client_loop(session, reader)
        # Should complete without raising


# ---------------------------------------------------------------------------
# _process_client_line — additional branches
# ---------------------------------------------------------------------------


class TestProcessClientLineAdditional:
    @pytest.mark.asyncio
    async def test_non_dict_json_sends_parse_error(self, tmp_path: Any) -> None:
        """A JSON array body triggers a parse error."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        await server._process_client_line(session, "[1, 2, 3]")

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_float_id_sends_parse_error(self, tmp_path: Any) -> None:
        """A float request ID is rejected with a parse error."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 1.5, "method": "tools/list"})
        await server._process_client_line(session, request)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_string_id_mapping_is_released_after_response(self, tmp_path: Any) -> None:
        """A completed string-ID request releases alias maps and reallocates safely."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": "stable-id", "method": "tools/list"})
        await server._process_client_line(session, request)
        first_alias = session.string_id_map.get("stable-id")
        assert first_alias is not None
        first_broker_id = (1 << _SESSION_SHIFT) | first_alias

        response = json.dumps({"jsonrpc": "2.0", "id": first_broker_id, "result": {}})
        await server.route_upstream_response(response)

        assert session.string_id_map == {}
        assert session.id_restore == {}
        assert session.pending == {}

        await server._process_client_line(session, request)
        second_alias = session.string_id_map.get("stable-id")
        assert second_alias is not None
        assert second_alias != first_alias

    @pytest.mark.asyncio
    async def test_upstream_write_failure_returns_32001(self, tmp_path: Any) -> None:
        """If upstream stdin.drain raises, client gets a -32001 error."""
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        daemon._upstream.stdin.drain = AsyncMock(side_effect=OSError("pipe broken"))
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Should have received a -32001 error
        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001
        assert session.pending == {}
        assert session.id_restore == {}
        assert session.int_id_map == {}
        assert session.string_id_map == {}

    @pytest.mark.asyncio
    async def test_upstream_write_failure_records_tool_failure_metrics(self, tmp_path: Any) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        daemon._upstream.stdin.drain = AsyncMock(side_effect=OSError("pipe broken"))
        metrics = MagicMock()
        audit = MagicMock()
        server = UnixSocketServer(cfg, daemon, metrics=metrics, audit=audit)
        session = _make_session(1)
        server._sessions[1] = session

        with patch(
            "mcpbridge_wrapper.broker.transport.time.time",
            side_effect=[1000.0, 1000.1, 1000.3],
        ):
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "BuildProject"},
                }
            )
            await server._process_client_line(session, request)

        metrics.record_response.assert_called_once()
        response_call = metrics.record_response.call_args
        assert response_call.args[0] == "BuildProject"
        assert response_call.kwargs["error"] is True
        assert response_call.kwargs["error_code"] == -32001
        assert response_call.kwargs["error_message"] == "Upstream write failed"
        assert response_call.kwargs["latency_ms"] == pytest.approx(300.0)
        audit.log.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnecting_then_unavailable_returns_32001(self, tmp_path: Any) -> None:
        """Gate passes (upstream_initialized set) but state is STOPPING → -32001."""
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock(state=BrokerState.STOPPING)
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        await server._process_client_line(session, request)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001


# ---------------------------------------------------------------------------
# Broker telemetry integration (FU-P13-T17)
# ---------------------------------------------------------------------------


class TestBrokerTelemetryIntegration:
    @pytest.mark.asyncio
    async def test_initialize_records_client_identity_in_metrics(self, tmp_path: Any) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        metrics = MagicMock()
        server = UnixSocketServer(cfg, daemon, metrics=metrics)
        session = _make_session(1)
        server._sessions[1] = session

        initialize_request = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"clientInfo": {"name": "Zed", "version": "1.0.0"}},
            }
        )
        await server._process_client_line(session, initialize_request)

        metrics.set_client_info.assert_called_once_with("Zed", "1.0.0")

    @pytest.mark.asyncio
    async def test_tools_call_records_request_and_response_metrics_with_audit(
        self, tmp_path: Any
    ) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        metrics = MagicMock()
        audit = MagicMock()
        server = UnixSocketServer(cfg, daemon, metrics=metrics, audit=audit)
        session = _make_session(1)
        server._sessions[1] = session

        with patch("mcpbridge_wrapper.broker.transport.time.time", side_effect=[1000.0, 1000.2]):
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 101,
                    "method": "tools/call",
                    "params": {
                        "name": "BuildProject",
                        "arguments": {"tabIdentifier": "windowtab1"},
                    },
                }
            )
            await server._process_client_line(session, request)

            local_alias = session.int_id_map[101]
            broker_id = (1 << _SESSION_SHIFT) | local_alias

            metrics.record_request.assert_called_once_with(
                "BuildProject",
                request_id=str(broker_id),
            )

            response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {"content": []}})
            await server.route_upstream_response(response)

        metrics.record_response.assert_called_once()
        response_call = metrics.record_response.call_args
        assert response_call.args[0] == "BuildProject"
        assert response_call.kwargs["request_id"] == str(broker_id)
        assert response_call.kwargs["error"] is False
        assert response_call.kwargs["latency_ms"] == pytest.approx(200.0)
        assert response_call.kwargs["error_code"] is None
        assert response_call.kwargs["error_message"] is None

        audit.log.assert_called_once()
        audit_call = audit.log.call_args
        assert audit_call.kwargs["tool_name"] == "BuildProject"
        assert audit_call.kwargs["request_id"] == str(broker_id)
        assert audit_call.kwargs["direction"] == "response"
        assert audit_call.kwargs["error"] is None
        assert audit_call.kwargs["error_code"] is None


class TestParseErrorDetails:
    def test_parse_error_details_from_jsonrpc_error_object(self) -> None:
        msg = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": "Internal error"}}
        is_error, error_code, error_message = UnixSocketServer._parse_error_details(msg)
        assert is_error is True
        assert error_code == -32603
        assert error_message == "Internal error"

    def test_parse_error_details_from_result_is_error_content(self) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "isError": True,
                "content": [
                    {"type": "text", "text": "Tool failed"},
                    {"type": "text", "text": "secondary"},
                ],
            },
        }
        is_error, error_code, error_message = UnixSocketServer._parse_error_details(msg)
        assert is_error is True
        assert error_code is None
        assert error_message == "Tool failed"


# ---------------------------------------------------------------------------
# _drain_session — string ID pending request
# ---------------------------------------------------------------------------


class TestDrainSession:
    @pytest.mark.asyncio
    async def test_drain_with_string_id_sends_string_in_error(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        session.string_id_map["my-req"] = 3
        session.id_restore[3] = "my-req"
        broker_id = (1 << _SESSION_SHIFT) | 3
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        session.pending[broker_id] = fut

        await server._drain_session(session)

        assert session.pending == {}
        assert fut.cancelled()
        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["id"] == "my-req"
        assert response["error"]["code"] == -32001
        assert session.id_restore == {}
        assert session.string_id_map == {}

    @pytest.mark.asyncio
    async def test_route_response_already_done_future_skipped(self, tmp_path: Any) -> None:
        """A future that is already done is not set again."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        broker_id = (1 << _SESSION_SHIFT) | 2
        session.int_id_map[777] = 2
        session.id_restore[2] = 777
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        fut.set_result("already done")
        session.pending[broker_id] = fut
        server._sessions[1] = session

        response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        # Should not raise InvalidStateError
        await server.route_upstream_response(response)
        assert session.id_restore == {}
        assert session.int_id_map == {}

    @pytest.mark.asyncio
    async def test_drain_session_records_broker_shutdown_failure_metrics(
        self, tmp_path: Any
    ) -> None:
        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock()
        metrics = MagicMock()
        audit = MagicMock()
        server = UnixSocketServer(cfg, daemon, metrics=metrics, audit=audit)
        session = _make_session(1)
        session.int_id_map[77] = 3
        session.id_restore[3] = 77
        broker_id = (1 << _SESSION_SHIFT) | 3
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        session.pending[broker_id] = fut
        server._pending_tool_requests[broker_id] = ("BuildProject", 1000.0)

        with patch("mcpbridge_wrapper.broker.transport.time.time", return_value=1000.4):
            await server._drain_session(session)

        metrics.record_response.assert_called_once()
        response_call = metrics.record_response.call_args
        assert response_call.args[0] == "BuildProject"
        assert response_call.kwargs["error"] is True
        assert response_call.kwargs["error_code"] == -32001
        assert response_call.kwargs["error_message"] == "Broker shutting down"
        assert response_call.kwargs["latency_ms"] == pytest.approx(400.0)
        assert broker_id not in server._pending_tool_requests
        audit.log.assert_called_once()


# ---------------------------------------------------------------------------
# FU-P13-T11 — Reversible per-session integer ID mapping
# ---------------------------------------------------------------------------


class TestIntegerIDFidelity:
    """Verify that integer request IDs of all shapes round-trip exactly."""

    @pytest.mark.asyncio
    async def test_large_integer_id_round_trips(self, tmp_path: Any) -> None:
        """An integer ID larger than 20 bits is preserved exactly."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        large_id = 2**21  # 2,097,152 — exceeds 20-bit mask
        request = json.dumps({"jsonrpc": "2.0", "id": large_id, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Forward map should record it
        assert large_id in session.int_id_map
        local_alias = session.int_id_map[large_id]
        broker_id = (1 << _SESSION_SHIFT) | local_alias

        # Simulate upstream response
        resp = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        await server.route_upstream_response(resp)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        decoded = json.loads(call_bytes.rstrip(b"\n"))
        assert decoded["id"] == large_id
        assert session.id_restore == {}
        assert session.int_id_map == {}

    @pytest.mark.asyncio
    async def test_negative_integer_id_round_trips(self, tmp_path: Any) -> None:
        """A negative integer ID is preserved exactly (not mangled by bitmask)."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        neg_id = -1
        request = json.dumps({"jsonrpc": "2.0", "id": neg_id, "method": "tools/list"})
        await server._process_client_line(session, request)

        assert neg_id in session.int_id_map
        local_alias = session.int_id_map[neg_id]
        broker_id = (1 << _SESSION_SHIFT) | local_alias

        resp = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        await server.route_upstream_response(resp)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        decoded = json.loads(call_bytes.rstrip(b"\n"))
        assert decoded["id"] == neg_id
        assert session.id_restore == {}
        assert session.int_id_map == {}

    @pytest.mark.asyncio
    async def test_concurrent_int_ids_no_collision(self, tmp_path: Any) -> None:
        """Two integer IDs whose lower 20 bits match get distinct broker IDs."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        id_a = 1
        id_b = 1 + (1 << _SESSION_SHIFT)  # same lower 20 bits as 1

        req_a = json.dumps({"jsonrpc": "2.0", "id": id_a, "method": "tools/list"})
        req_b = json.dumps({"jsonrpc": "2.0", "id": id_b, "method": "tools/list"})
        await server._process_client_line(session, req_a)
        await server._process_client_line(session, req_b)

        alias_a = session.int_id_map[id_a]
        alias_b = session.int_id_map[id_b]
        assert alias_a != alias_b, "distinct original IDs must get distinct local aliases"

        broker_a = (1 << _SESSION_SHIFT) | alias_a
        broker_b = (1 << _SESSION_SHIFT) | alias_b
        assert broker_a != broker_b

    @pytest.mark.asyncio
    async def test_integer_id_mapping_is_released_after_response(self, tmp_path: Any) -> None:
        """A completed integer-ID request releases alias maps and reallocates safely."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": 42, "method": "tools/list"})
        await server._process_client_line(session, request)
        alias_first = session.int_id_map.get(42)
        assert alias_first is not None
        broker_id = (1 << _SESSION_SHIFT) | alias_first

        await server.route_upstream_response(
            json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        )
        assert session.int_id_map == {}
        assert session.id_restore == {}
        assert session.pending == {}

        await server._process_client_line(session, request)
        alias_second = session.int_id_map.get(42)
        assert alias_second is not None
        assert alias_second != alias_first

    @pytest.mark.asyncio
    async def test_int_and_string_id_no_collision(self, tmp_path: Any) -> None:
        """Integer 1 and a string ID do not receive the same local alias."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        req_int = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        req_str = json.dumps({"jsonrpc": "2.0", "id": "call-1", "method": "tools/list"})
        await server._process_client_line(session, req_int)
        await server._process_client_line(session, req_str)

        int_alias = session.int_id_map.get(1)
        str_alias = session.string_id_map.get("call-1")
        assert int_alias is not None
        assert str_alias is not None
        assert int_alias != str_alias, "int and string IDs must not share a local alias"


class TestP14T1MapBounding:
    @pytest.mark.asyncio
    async def test_maps_remain_bounded_for_completed_request_stream(self, tmp_path: Any) -> None:
        """Completed requests should not leave historical alias entries behind."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        for request_id in range(1, 129):
            request = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": "tools/list"})
            await server._process_client_line(session, request)
            local_alias = session.int_id_map[request_id]
            broker_id = (1 << _SESSION_SHIFT) | local_alias
            await server.route_upstream_response(
                json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {"ok": True}})
            )

            assert session.pending == {}
            assert session.id_restore == {}
            assert session.int_id_map == {}
            assert session.string_id_map == {}

    def test_alloc_local_id_skips_active_aliases_after_wrap(self) -> None:
        """When the counter wraps, allocator skips aliases still in use."""
        session = _make_session(1)
        session._next_local_id = _ID_MASK
        session.id_restore[1] = "active"

        allocated = _alloc_local_id(session)
        assert allocated == 2


# ---------------------------------------------------------------------------
# FU-P13-T12: Peer credential verification
# ---------------------------------------------------------------------------


class TestGetPeerUID:
    """Unit coverage for platform-specific peer credential resolution."""

    def test_get_peer_uid_prefers_getpeereid(self) -> None:
        """When available, getpeereid() is used directly."""
        expected_uid = 501
        fake_socket = MagicMock()
        fake_socket.getpeereid.return_value = (expected_uid, 20)
        writer = MagicMock()
        writer.get_extra_info.return_value = fake_socket

        uid = _get_peer_uid(writer)
        assert uid == expected_uid
        fake_socket.getpeereid.assert_called_once_with()

    def test_get_peer_uid_uses_local_peercred_when_getpeereid_missing(self) -> None:
        """LOCAL_PEERCRED fallback extracts uid on BSD/macOS-style sockets."""

        class SocketWithoutGetPeerEid:
            def __init__(self, creds: bytes) -> None:
                self._creds = creds
                self.last_call: tuple[int, int, int] | None = None

            def getsockopt(self, level: int, optname: int, buflen: int) -> bytes:
                self.last_call = (level, optname, buflen)
                return self._creds

        expected_uid = 501
        creds = struct.pack("3i", 0, expected_uid, 0)
        fake_socket = SocketWithoutGetPeerEid(creds)
        writer = MagicMock()
        writer.get_extra_info.return_value = fake_socket

        with patch.object(transport_module.socket, "LOCAL_PEERCRED", 1, create=True), patch.object(
            transport_module.socket, "SOL_LOCAL", 0, create=True
        ), patch.object(transport_module.socket, "SO_PEERCRED", None, create=True):
            uid = _get_peer_uid(writer)

        assert uid == expected_uid
        assert fake_socket.last_call == (0, 1, struct.calcsize("3i"))

    def test_get_peer_uid_uses_so_peercred_when_available(self) -> None:
        """SO_PEERCRED fallback extracts uid on Linux-style sockets."""

        class SocketWithPeerCred:
            def __init__(self, creds: bytes) -> None:
                self._creds = creds
                self.last_call: tuple[int, int, int] | None = None

            def getsockopt(self, level: int, optname: int, buflen: int) -> bytes:
                self.last_call = (level, optname, buflen)
                return self._creds

        expected_uid = 501
        creds = struct.pack("3i", 12345, expected_uid, 20)
        fake_socket = SocketWithPeerCred(creds)
        writer = MagicMock()
        writer.get_extra_info.return_value = fake_socket

        with patch.object(
            transport_module.socket,
            "LOCAL_PEERCRED",
            None,
            create=True,
        ), patch.object(
            transport_module.socket,
            "SO_PEERCRED",
            17,
            create=True,
        ):
            uid = _get_peer_uid(writer)

        assert uid == expected_uid
        assert fake_socket.last_call == (socket.SOL_SOCKET, 17, struct.calcsize("3i"))

    def test_get_peer_uid_raises_when_no_supported_api(self) -> None:
        """Unsupported platforms raise OSError so callers can fail-closed."""

        class SocketWithoutCredentialAPIs:
            pass

        writer = MagicMock()
        writer.get_extra_info.return_value = SocketWithoutCredentialAPIs()

        with patch.object(
            transport_module.socket,
            "LOCAL_PEERCRED",
            None,
            create=True,
        ), patch.object(
            transport_module.socket,
            "SO_PEERCRED",
            None,
            create=True,
        ), pytest.raises(
            OSError,
            match="No supported peer credential API available",
        ):
            _get_peer_uid(writer)


class TestPeerCredentialVerification:
    """UID-based peer credential enforcement in _handle_client (FU-P13-T12)."""

    @pytest.mark.asyncio
    async def test_same_uid_client_accepted(self, tmp_path: Any) -> None:
        """Client with matching UID passes verification and enters the read loop."""
        server = _make_server(tmp_path)
        own_uid = os.getuid()

        writer = _make_writer()
        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b"")  # EOF immediately

        with patch(
            "mcpbridge_wrapper.broker.transport._get_peer_uid",
            return_value=own_uid,
        ):
            await server._handle_client(reader, writer)

        # reader.readline must have been called — proof the read loop ran
        reader.readline.assert_called()
        # No -32003 error should have been sent
        all_data = b"".join(call[0][0] for call in writer.write.call_args_list)
        assert b"-32003" not in all_data

    @pytest.mark.asyncio
    async def test_different_uid_client_rejected(self, tmp_path: Any) -> None:
        """Client with non-matching UID receives -32003 error and connection is closed."""
        server = _make_server(tmp_path)
        own_uid = os.getuid()
        foreign_uid = own_uid + 1

        writer = _make_writer()
        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b"")  # must not be reached

        with patch(
            "mcpbridge_wrapper.broker.transport._get_peer_uid",
            return_value=foreign_uid,
        ):
            await server._handle_client(reader, writer)

        # -32003 error must have been written
        all_data = b"".join(call[0][0] for call in writer.write.call_args_list)
        msg = json.loads(all_data.rstrip(b"\n"))
        assert msg["error"]["code"] == -32003
        # Writer must be closed
        writer.close.assert_called()
        # Read loop must NOT have run
        reader.readline.assert_not_called()
        # Session must NOT be registered
        assert len(server.sessions) == 0

    @pytest.mark.asyncio
    async def test_peer_uid_stored_on_session(self, tmp_path: Any) -> None:
        """Accepted client's UID is stored on the resulting ClientSession."""
        server = _make_server(tmp_path)
        own_uid = os.getuid()

        captured: list[ClientSession] = []

        async def capture_loop(session: ClientSession, reader: Any) -> None:
            captured.append(session)
            # Return immediately (simulate EOF)

        writer = _make_writer()
        reader = MagicMock()

        with patch(
            "mcpbridge_wrapper.broker.transport._get_peer_uid",
            return_value=own_uid,
        ), patch.object(server, "_read_client_loop", capture_loop):
            await server._handle_client(reader, writer)

        assert len(captured) == 1, "Read loop should have been entered once"
        assert captured[0].peer_uid == own_uid

    @pytest.mark.asyncio
    async def test_uid_check_failure_is_rejected(self, tmp_path: Any) -> None:
        """If UID retrieval raises OSError, connection is rejected defensively (fail-closed)."""
        server = _make_server(tmp_path)

        writer = _make_writer()
        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b"")  # must not be reached

        with patch(
            "mcpbridge_wrapper.broker.transport._get_peer_uid",
            side_effect=OSError("Not supported on this platform"),
        ):
            await server._handle_client(reader, writer)

        # -32003 error must have been written
        all_data = b"".join(call[0][0] for call in writer.write.call_args_list)
        msg = json.loads(all_data.rstrip(b"\n"))
        assert msg["error"]["code"] == -32003
        writer.close.assert_called()
        reader.readline.assert_not_called()
        assert len(server.sessions) == 0


# ---------------------------------------------------------------------------
# FU-P13-T12: Socket file permissions
# ---------------------------------------------------------------------------


class TestSocketPermissions:
    """Socket file must be created with 0600 permissions (FU-P13-T12)."""

    @pytest.mark.asyncio
    async def test_socket_created_with_0600_permissions(self) -> None:
        """After start(), the socket file has owner-only read/write permissions."""
        short_dir = tempfile.mkdtemp(dir="/tmp", prefix="mcpb")
        server = _make_server(short_dir)
        try:
            await server.start()
            try:
                socket_path = os.path.join(short_dir, "broker.sock")
                mode = stat.S_IMODE(os.stat(socket_path).st_mode)
                assert mode == 0o600, f"Expected 0600, got {oct(mode)}"
            finally:
                await server.stop()
        finally:
            shutil.rmtree(short_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# P4-T2: tools/list cache and upstream readiness gate
# ---------------------------------------------------------------------------


class TestToolsListCache:
    """P4-T2 — tools/list served from broker cache when available."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self, tmp_path: Any) -> None:
        """When _tools_list_cache is set, tools/list is served from cache (no upstream write)."""
        import json as _json

        cached_result = {"tools": [{"name": "BuildProject"}, {"name": "RunTests"}]}
        cached_raw = _json.dumps({"jsonrpc": "2.0", "id": -1, "result": cached_result})

        server = _make_server(tmp_path)
        daemon = server._daemon
        daemon._tools_list_cache = cached_raw

        session = _make_session(1)
        server._sessions[1] = session

        request = _json.dumps({"jsonrpc": "2.0", "id": 42, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Upstream stdin must NOT have been written — served from cache.
        daemon._upstream.stdin.write.assert_not_called()

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = _json.loads(call_bytes.rstrip(b"\n"))
        assert response["id"] == 42
        assert response["result"] == cached_result

    @pytest.mark.asyncio
    async def test_cache_hit_with_string_id(self, tmp_path: Any) -> None:
        """Cache hit works with string client IDs and restores the original ID."""
        import json as _json

        cached_raw = _json.dumps({"jsonrpc": "2.0", "id": -1, "result": {"tools": []}})

        server = _make_server(tmp_path)
        daemon = server._daemon
        daemon._tools_list_cache = cached_raw

        session = _make_session(1)
        server._sessions[1] = session

        request = _json.dumps({"jsonrpc": "2.0", "id": "req-abc", "method": "tools/list"})
        await server._process_client_line(session, request)

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = _json.loads(call_bytes.rstrip(b"\n"))
        assert response["id"] == "req-abc"

    @pytest.mark.asyncio
    async def test_cache_miss_forwards_to_upstream(self, tmp_path: Any) -> None:
        """When _tools_list_cache is None, tools/list is forwarded to upstream."""
        import json as _json

        server = _make_server(tmp_path)
        daemon = server._daemon
        assert daemon._tools_list_cache is None  # default fixture value

        session = _make_session(1)
        server._sessions[1] = session

        request = _json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/list"})
        await server._process_client_line(session, request)

        # Request was forwarded to upstream stdin.
        daemon._upstream.stdin.write.assert_called()
