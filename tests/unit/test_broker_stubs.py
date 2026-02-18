"""Tests for the broker module scaffold (P13-T1 stubs).

These tests verify that the stub classes and types are importable, have the
correct structure, and raise NotImplementedError as expected. Full behaviour
tests will be added in P13-T2 through P13-T4.
"""

from __future__ import annotations

import asyncio
import enum
import time
from dataclasses import fields
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcpbridge_wrapper.broker import (
    BrokerConfig,
    BrokerDaemon,
    BrokerProxy,
    BrokerState,
    ClientSession,
    PendingRequest,
    UnixSocketServer,
)

# ---------------------------------------------------------------------------
# BrokerState
# ---------------------------------------------------------------------------


class TestBrokerState:
    def test_is_enum(self) -> None:
        assert issubclass(BrokerState, enum.Enum)

    def test_expected_members(self) -> None:
        names = {m.name for m in BrokerState}
        assert names == {"INIT", "READY", "RECONNECTING", "STOPPING", "STOPPED"}

    def test_values_are_strings(self) -> None:
        for member in BrokerState:
            assert isinstance(member.value, str)


# ---------------------------------------------------------------------------
# BrokerConfig
# ---------------------------------------------------------------------------


class TestBrokerConfig:
    def test_default_factory(self) -> None:
        cfg = BrokerConfig.default()
        assert isinstance(cfg.socket_path, Path)
        assert isinstance(cfg.pid_file, Path)
        assert cfg.socket_path.name == "broker.sock"
        assert cfg.pid_file.name == "broker.pid"
        assert cfg.upstream_cmd == ["xcrun", "mcpbridge"]

    def test_default_backoff_cap(self) -> None:
        cfg = BrokerConfig.default()
        assert cfg.reconnect_backoff_cap == 30

    def test_default_queue_ttl(self) -> None:
        cfg = BrokerConfig.default()
        assert cfg.queue_ttl == 60

    def test_default_graceful_shutdown_timeout(self) -> None:
        cfg = BrokerConfig.default()
        assert cfg.graceful_shutdown_timeout == 5

    def test_custom_values(self) -> None:
        cfg = BrokerConfig(
            socket_path=Path("/tmp/test.sock"),
            pid_file=Path("/tmp/test.pid"),
            upstream_cmd=["my-bridge"],
            reconnect_backoff_cap=10,
            queue_ttl=30,
            graceful_shutdown_timeout=2,
        )
        assert cfg.socket_path == Path("/tmp/test.sock")
        assert cfg.upstream_cmd == ["my-bridge"]

    def test_field_names(self) -> None:
        field_names = {f.name for f in fields(BrokerConfig)}
        assert "socket_path" in field_names
        assert "pid_file" in field_names
        assert "upstream_cmd" in field_names


# ---------------------------------------------------------------------------
# ClientSession
# ---------------------------------------------------------------------------


class TestClientSession:
    def _make(self) -> ClientSession:
        return ClientSession(
            session_id=1,
            peer_uid=501,
            connected_at=time.time(),
            writer=MagicMock(),
        )

    def test_pending_defaults_to_empty_dict(self) -> None:
        session = self._make()
        assert session.pending == {}

    def test_string_id_map_defaults_to_empty_dict(self) -> None:
        session = self._make()
        assert session.string_id_map == {}

    def test_fields_accessible(self) -> None:
        session = self._make()
        assert session.session_id == 1
        assert session.peer_uid == 501

    def test_two_sessions_have_independent_pending_dicts(self) -> None:
        s1 = self._make()
        s2 = self._make()
        s1.pending[1] = MagicMock()
        assert 1 not in s2.pending


# ---------------------------------------------------------------------------
# PendingRequest
# ---------------------------------------------------------------------------


class TestPendingRequest:
    def test_fields(self) -> None:
        req = PendingRequest(
            client_id=3,
            original_id=42,
            broker_id=(3 << 20) | 42,
            queued_at=time.time(),
        )
        assert req.client_id == 3
        assert req.original_id == 42
        assert req.broker_id == (3 << 20) | 42

    def test_string_original_id(self) -> None:
        req = PendingRequest(
            client_id=1,
            original_id="abc-123",
            broker_id=100,
            queued_at=time.time(),
        )
        assert req.original_id == "abc-123"


# ---------------------------------------------------------------------------
# BrokerDaemon stubs
# ---------------------------------------------------------------------------


class TestBrokerDaemonStubs:
    def setup_method(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.cfg = BrokerConfig.default()
        self.daemon = BrokerDaemon(self.cfg)

    def teardown_method(self) -> None:
        self.loop.close()
        asyncio.set_event_loop(None)

    def test_initial_state_is_init(self) -> None:
        assert self.daemon.state == BrokerState.INIT

    # NOTE: start/stop/run_forever are implemented in P13-T2.
    # Detailed behaviour tests live in tests/unit/test_broker_daemon.py.


# ---------------------------------------------------------------------------
# UnixSocketServer — basic instantiation (full tests in test_broker_transport.py)
# ---------------------------------------------------------------------------


class TestUnixSocketServerInstantiation:
    def setup_method(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.cfg = BrokerConfig.default()
        self.daemon_mock = MagicMock()
        self.daemon_mock.state = BrokerState.READY
        self.server = UnixSocketServer(self.cfg, self.daemon_mock)

    def teardown_method(self) -> None:
        self.loop.close()
        asyncio.set_event_loop(None)

    def test_instantiation_succeeds(self) -> None:
        assert self.server is not None

    def test_sessions_initially_empty(self) -> None:
        assert self.server.sessions == {}


# ---------------------------------------------------------------------------
# BrokerProxy — basic contract (P13-T4 full implementation)
# ---------------------------------------------------------------------------


class TestBrokerProxyBasic:
    def setup_method(self) -> None:
        self.cfg = BrokerConfig.default()
        self.proxy = BrokerProxy(self.cfg, connect_timeout=0.1)

    def test_instantiation_succeeds(self) -> None:
        assert self.proxy is not None

    @pytest.mark.asyncio
    async def test_run_raises_timeout_when_no_socket(self) -> None:
        """run() raises TimeoutError when broker socket is absent."""
        with pytest.raises(TimeoutError):
            await self.proxy.run()


# ---------------------------------------------------------------------------
# __init__ public API
# ---------------------------------------------------------------------------


class TestBrokerPublicAPI:
    def test_all_exports_present(self) -> None:
        import mcpbridge_wrapper.broker as broker_pkg

        for name in [
            "BrokerConfig",
            "BrokerDaemon",
            "BrokerProxy",
            "BrokerState",
            "ClientSession",
            "PendingRequest",
            "UnixSocketServer",
        ]:
            assert hasattr(broker_pkg, name), f"Missing export: {name}"
