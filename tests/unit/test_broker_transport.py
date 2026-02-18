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
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpbridge_wrapper.broker.transport import _ID_MASK, _SESSION_SHIFT, UnixSocketServer
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

        expected_broker_id = (2 << _SESSION_SHIFT) | 10
        written = session.pending
        assert expected_broker_id in written

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
        cfg = _make_config(tmp_path)
        # queue_ttl = 2 from _make_config; we'll force immediate expiry
        cfg = BrokerConfig(
            socket_path=cfg.socket_path,
            pid_file=cfg.pid_file,
            upstream_cmd=["true"],
            reconnect_backoff_cap=1,
            queue_ttl=0,  # immediate expiry
            graceful_shutdown_timeout=1,
        )
        daemon = _make_daemon_mock(state=BrokerState.RECONNECTING)
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
    async def test_reconnect_becomes_ready_proceeds(self, tmp_path: Any) -> None:
        """When daemon transitions RECONNECTING → READY, request is forwarded."""
        from unittest.mock import PropertyMock

        cfg = _make_config(tmp_path)
        daemon = _make_daemon_mock(state=BrokerState.RECONNECTING)
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        # Call sequence:
        # 1. daemon_state = self._daemon.state  → RECONNECTING (enters reconnect branch)
        # 2. while self._daemon.state == RECONNECTING  → RECONNECTING (loop body runs once)
        # 3. while self._daemon.state == RECONNECTING  → READY (exits while loop)
        # 4. if self._daemon.state not in (READY,)  → READY (does NOT return error)
        state_sequence = [
            BrokerState.RECONNECTING,
            BrokerState.RECONNECTING,
            BrokerState.READY,
            BrokerState.READY,
        ]
        state_mock = PropertyMock(side_effect=state_sequence)
        type(daemon).state = state_mock

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
    async def test_string_id_reuses_existing_alias(self, tmp_path: Any) -> None:
        """Sending the same string ID twice reuses the same integer alias."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        server._sessions[1] = session

        request = json.dumps({"jsonrpc": "2.0", "id": "stable-id", "method": "tools/list"})
        # Send twice
        await server._process_client_line(session, request)
        first_alias = session.string_id_map.get("stable-id")

        await server._process_client_line(session, request)
        second_alias = session.string_id_map.get("stable-id")

        assert first_alias == second_alias
        assert first_alias is not None

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

    @pytest.mark.asyncio
    async def test_reconnecting_then_unavailable_returns_32001(self, tmp_path: Any) -> None:
        """After reconnect wait, if state is not READY, return -32001."""
        cfg = _make_config(tmp_path)
        cfg = BrokerConfig(
            socket_path=cfg.socket_path,
            pid_file=cfg.pid_file,
            upstream_cmd=["true"],
            reconnect_backoff_cap=1,
            queue_ttl=5,
            graceful_shutdown_timeout=1,
        )
        daemon = _make_daemon_mock(state=BrokerState.RECONNECTING)
        server = UnixSocketServer(cfg, daemon)
        session = _make_session(1)
        server._sessions[1] = session

        call_count = 0

        def state_side_effect(obj: Any) -> BrokerState:
            nonlocal call_count
            call_count += 1
            # First call in daemon_state check
            if call_count == 1:
                return BrokerState.RECONNECTING
            # While loop check — immediately exit by returning non-RECONNECTING
            if call_count == 2:
                return BrokerState.STOPPING  # not RECONNECTING, exits while loop
            return BrokerState.STOPPING

        type(daemon).state = property(state_side_effect)
        try:
            request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            await server._process_client_line(session, request)
        finally:
            del type(daemon).state

        call_bytes: bytes = session.writer.write.call_args[0][0]
        response = json.loads(call_bytes.rstrip(b"\n"))
        assert response["error"]["code"] == -32001


# ---------------------------------------------------------------------------
# _drain_session — string ID pending request
# ---------------------------------------------------------------------------


class TestDrainSession:
    @pytest.mark.asyncio
    async def test_drain_with_string_id_sends_string_in_error(self, tmp_path: Any) -> None:
        server = _make_server(tmp_path)
        session = _make_session(1)
        session.string_id_map["my-req"] = 3
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

    @pytest.mark.asyncio
    async def test_route_response_already_done_future_skipped(self, tmp_path: Any) -> None:
        """A future that is already done is not set again."""
        server = _make_server(tmp_path)
        session = _make_session(1)
        broker_id = (1 << _SESSION_SHIFT) | 2
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[str] = loop.create_future()
        fut.set_result("already done")
        session.pending[broker_id] = fut
        server._sessions[1] = session

        response = json.dumps({"jsonrpc": "2.0", "id": broker_id, "result": {}})
        # Should not raise InvalidStateError
        await server.route_upstream_response(response)
