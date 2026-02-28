"""Unit tests for BrokerProxy — P13-T4 implementation.

Covers:
- connect_timeout: raises TimeoutError when socket absent
- Successful bidirectional forwarding (stdin→socket, socket→stdout)
- EOF on stdin causes clean exit without signalling broker
- EOF on socket causes clean exit
- auto_spawn: spawns broker subprocess when socket absent
- auto_spawn: no-op when broker already running (PID file present)
- _parse_broker_args: --broker-connect flag
- _parse_broker_args: --broker-spawn implies --broker-connect
- _parse_broker_args: unknown flags pass through
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpbridge_wrapper.__main__ import _parse_broker_args
from mcpbridge_wrapper.broker.proxy import BrokerProxy
from mcpbridge_wrapper.broker.types import BrokerConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path) -> BrokerConfig:
    # Unix domain socket paths on macOS are limited to ~104 chars.
    # Use /tmp directly with a short unique suffix to stay well within the limit.
    import tempfile

    short_dir = Path(tempfile.mkdtemp(dir="/tmp", prefix="mcp"))
    return BrokerConfig(
        socket_path=short_dir / "b.sock",
        pid_file=short_dir / "b.pid",
        upstream_cmd=["true"],
        reconnect_backoff_cap=1,
        queue_ttl=2,
        graceful_shutdown_timeout=1,
    )


def _make_reader(lines: list[bytes]) -> asyncio.StreamReader:
    """Create a StreamReader pre-loaded with the given lines (empty bytes = EOF)."""
    reader = asyncio.StreamReader()
    for line in lines:
        if line:
            reader.feed_data(line)
    reader.feed_eof()
    return reader


def _make_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


# ---------------------------------------------------------------------------
# connect timeout
# ---------------------------------------------------------------------------


class TestBrokerProxyConnectTimeout:
    def test_constructor_has_no_reconnect_parameter(self) -> None:
        params = inspect.signature(BrokerProxy.__init__).parameters
        assert "reconnect" not in params

    @pytest.mark.asyncio
    async def test_raises_timeout_when_no_socket(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, connect_timeout=0.1)
        with pytest.raises(TimeoutError):
            await proxy.run()


# ---------------------------------------------------------------------------
# Bidirectional forwarding
# ---------------------------------------------------------------------------


class TestBrokerProxyForwarding:
    @pytest.mark.asyncio
    async def test_stdin_to_socket(self, tmp_path: Path) -> None:
        """Lines read from stdin are forwarded to the socket writer."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n'])
        sock_reader = _make_reader([])  # EOF immediately
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ):
            await proxy.run()

        # Verify stdin line was written to the socket
        sock_writer.write.assert_called_once_with(b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n')

    @pytest.mark.asyncio
    async def test_socket_to_stdout(self, tmp_path: Path) -> None:
        """Lines received from the socket are written to stdout."""
        cfg = _make_config(tmp_path)
        response = b'{"jsonrpc":"2.0","id":1,"result":{}}\n'
        stdin_reader = _make_reader([])  # EOF immediately
        sock_reader = _make_reader([response])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ):
            await proxy.run()

        stdout_writer.write.assert_called_once_with(response)


# ---------------------------------------------------------------------------
# EOF / clean exit — broker not signalled
# ---------------------------------------------------------------------------


class TestBrokerProxyEOF:
    @pytest.mark.asyncio
    async def test_stdin_eof_closes_socket_only(self, tmp_path: Path) -> None:
        """Socket writer is closed on stdin EOF; no other side-effects."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])  # immediate EOF
        sock_reader = _make_reader([b"line\n"])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ):
            await proxy.run()

        sock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_socket_eof_exits_cleanly(self, tmp_path: Path) -> None:
        """Proxy exits without error when the socket reaches EOF."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([b"line\n"])
        sock_reader = _make_reader([])  # immediate EOF
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ):
            # Should return cleanly, no exception
            await proxy.run()


# ---------------------------------------------------------------------------
# auto_spawn
# ---------------------------------------------------------------------------


class TestBrokerProxyAutoSpawn:
    @pytest.mark.asyncio
    async def test_spawn_called_when_socket_absent(self, tmp_path: Path) -> None:
        """When auto_spawn=True and socket absent, _spawn_broker_if_needed is called."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])
        sock_reader = _make_reader([])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            auto_spawn=True,
            connect_timeout=0.1,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        spawn_called = []

        async def fake_spawn() -> None:
            spawn_called.append(True)

        with patch.object(proxy, "_spawn_broker_if_needed", fake_spawn), patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ):
            await proxy.run()

        assert spawn_called == [True]

    @pytest.mark.asyncio
    async def test_spawn_noop_when_pid_file_live(self, tmp_path: Path) -> None:
        """_spawn_broker_if_needed does nothing when a live PID file exists."""
        cfg = _make_config(tmp_path)
        # Write own PID (current process is live)
        cfg.pid_file.write_text(str(os.getpid()))

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.1)

        with patch("subprocess.Popen") as mock_popen:
            # _spawn_broker_if_needed should return without calling Popen
            await proxy._spawn_broker_if_needed()

        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_spawn_noop_when_socket_exists(self, tmp_path: Path) -> None:
        """_spawn_broker_if_needed does nothing when socket file already exists."""
        cfg = _make_config(tmp_path)
        cfg.socket_path.touch()  # simulate running broker

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.1)

        with patch("subprocess.Popen") as mock_popen:
            await proxy._spawn_broker_if_needed()

        mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_spawn_raises_timeout_if_socket_never_appears(self, tmp_path: Path) -> None:
        """_spawn_broker_if_needed raises TimeoutError if socket never appears."""
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.3)

        with patch("subprocess.Popen"), pytest.raises(TimeoutError):
            await proxy._spawn_broker_if_needed()

    @pytest.mark.asyncio
    async def test_spawn_uses_custom_spawn_args(self, tmp_path: Path) -> None:
        """Custom spawn args are propagated to daemon launch command."""
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(
            cfg,
            auto_spawn=True,
            connect_timeout=1.0,
            spawn_args=["--web-ui", "--web-ui-port", "9090"],
        )

        real_exists = Path.exists
        socket_checks = {"count": 0}

        def _fake_exists(path_obj: Path) -> bool:
            if path_obj == cfg.pid_file:
                return False
            if path_obj == cfg.socket_path:
                socket_checks["count"] += 1
                return socket_checks["count"] >= 2
            return real_exists(path_obj)

        with patch.object(Path, "exists", _fake_exists), patch("subprocess.Popen") as mock_popen:
            await proxy._spawn_broker_if_needed()

        cmd = mock_popen.call_args.args[0]
        assert cmd[:3] == [sys.executable, "-m", "mcpbridge_wrapper"]
        assert cmd[3:] == ["--broker-daemon", "--web-ui", "--web-ui-port", "9090"]


# ---------------------------------------------------------------------------
# _parse_broker_args
# ---------------------------------------------------------------------------


class TestParseBrokerArgs:
    def test_no_flags_leaves_all_args(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--some-flag", "value"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--some-flag", "value"]

    def test_broker_connect_flag(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-connect"])
        assert daemon is False
        assert connect is True
        assert spawn is False
        assert remaining == []

    def test_broker_spawn_implies_connect(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-spawn"])
        assert daemon is False
        assert connect is True
        assert spawn is True
        assert remaining == []

    def test_unknown_flags_pass_through(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(
            ["--broker-connect", "--other-flag", "val"]
        )
        assert daemon is False
        assert connect is True
        assert remaining == ["--other-flag", "val"]

    def test_both_flags_together(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(
            ["--broker-connect", "--broker-spawn"]
        )
        assert daemon is False
        assert connect is True
        assert spawn is True
        assert remaining == []

    def test_empty_args(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args([])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == []

    def test_broker_daemon_flag(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-daemon"])
        assert daemon is True
        assert connect is False
        assert spawn is False
        assert remaining == []

    def test_broker_daemon_not_in_remaining(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-daemon", "--other-flag"])
        assert daemon is True
        assert "--broker-daemon" not in remaining
        assert remaining == ["--other-flag"]
