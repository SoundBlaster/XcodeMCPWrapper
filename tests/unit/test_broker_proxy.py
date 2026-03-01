"""Unit tests for BrokerProxy — P13-T4 implementation.

Covers:
- connect_timeout: raises TimeoutError when socket absent
- Successful bidirectional forwarding (stdin→socket, socket→stdout)
- EOF on stdin causes clean exit without signalling broker
- EOF on socket causes clean exit
- auto_spawn: spawns broker subprocess when socket absent
- auto_spawn: no-op when broker already running (PID file present)
- _parse_broker_args: --broker enables spawn+connect
- _parse_broker_args: legacy broker flags pass through unchanged
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
    async def test_returns_with_error_when_no_socket(self, tmp_path: Path) -> None:
        """run() writes a JSON-RPC error and returns cleanly when no broker socket exists."""
        import json

        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()
        proxy = BrokerProxy(cfg, connect_timeout=0.1, stdout=stdout_writer)
        # run() must not raise — it catches the TimeoutError and writes an error response
        await proxy.run()
        assert stdout_writer.write.called
        raw = stdout_writer.write.call_args.args[0]
        response = json.loads(raw.decode())
        assert response["error"]["code"] == -32001


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
        """_spawn_broker_if_needed does nothing when socket file exists and broker is alive."""
        cfg = _make_config(tmp_path)
        cfg.socket_path.touch()  # simulate socket file present

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.1)

        # Mock socket.connect to succeed (broker is alive)
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "subprocess.Popen"
        ) as mock_popen:
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
# Stale socket recovery (P2-T2)
# ---------------------------------------------------------------------------


class TestBrokerProxyStaleSocket:
    @pytest.mark.asyncio
    async def test_stale_socket_triggers_spawn(self, tmp_path: Path) -> None:
        """When socket exists but connect raises OSError, spawn proceeds."""
        cfg = _make_config(tmp_path)
        cfg.socket_path.touch()  # stale socket file

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.3)

        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect.side_effect = ConnectionRefusedError

        with patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "subprocess.Popen"
        ) as mock_popen, pytest.raises(TimeoutError):
            # Socket never appears after spawn, so TimeoutError is expected
            await proxy._spawn_broker_if_needed()

        mock_popen.assert_called_once()

    @pytest.mark.asyncio
    async def test_stale_socket_removes_files(self, tmp_path: Path) -> None:
        """Stale socket and PID files are removed before attempting spawn."""
        cfg = _make_config(tmp_path)
        cfg.socket_path.touch()
        cfg.pid_file.write_text("99999")  # stale PID file

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.3)

        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect.side_effect = ConnectionRefusedError

        with patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "subprocess.Popen"
        ), pytest.raises(TimeoutError):
            await proxy._spawn_broker_if_needed()

        assert not cfg.socket_path.exists()
        assert not cfg.pid_file.exists()

    @pytest.mark.asyncio
    async def test_live_socket_skips_spawn(self, tmp_path: Path) -> None:
        """When socket exists and connect succeeds, spawn is skipped."""
        cfg = _make_config(tmp_path)
        cfg.socket_path.touch()

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.1)

        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        # connect() returns None (success)

        with patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "subprocess.Popen"
        ) as mock_popen:
            await proxy._spawn_broker_if_needed()

        mock_popen.assert_not_called()


# ---------------------------------------------------------------------------
# Spawn lock (P2-T3)
# ---------------------------------------------------------------------------


class TestBrokerProxySpawnLock:
    @pytest.mark.asyncio
    async def test_spawn_lock_file_created_next_to_pid_file(self, tmp_path: Path) -> None:
        """Lock file is created at pid_file.with_suffix('.lock')."""
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.3)

        with patch("subprocess.Popen"), pytest.raises(TimeoutError):
            await proxy._spawn_broker_if_needed()

        expected_lock = cfg.pid_file.with_suffix(".lock")
        assert expected_lock.exists()

    @pytest.mark.asyncio
    async def test_spawn_acquires_exclusive_lock(self, tmp_path: Path) -> None:
        """_spawn_broker_if_needed acquires LOCK_EX via fcntl.flock."""
        import fcntl as fcntl_module

        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.3)

        flock_calls: list[int] = []

        def fake_flock(fd: int, op: int) -> None:
            flock_calls.append(op)

        with patch("mcpbridge_wrapper.broker.proxy.fcntl.flock", fake_flock), patch(
            "subprocess.Popen"
        ), pytest.raises(TimeoutError):
            await proxy._spawn_broker_if_needed()

        assert fcntl_module.LOCK_EX in flock_calls

    @pytest.mark.asyncio
    async def test_second_proxy_skips_spawn_after_first_succeeds(self, tmp_path: Path) -> None:
        """Second proxy detects live socket under lock and skips Popen."""
        cfg = _make_config(tmp_path)
        popen_count = 0

        def fake_popen(*args: object, **kwargs: object) -> MagicMock:
            nonlocal popen_count
            popen_count += 1
            # Simulate first spawn: create the socket file so polling succeeds.
            cfg.socket_path.touch()
            return MagicMock()

        proxy1 = BrokerProxy(cfg, auto_spawn=True, connect_timeout=1.0)
        proxy2 = BrokerProxy(cfg, auto_spawn=True, connect_timeout=1.0)

        with patch("subprocess.Popen", side_effect=fake_popen):
            # First proxy spawns the daemon (socket appears during poll).
            await proxy1._spawn_broker_if_needed()
            # Second proxy acquires lock, re-checks, finds socket alive → skips Popen.
            # Mock connect to succeed so the socket-liveness check passes.
            mock_sock = MagicMock()
            mock_sock.__enter__ = MagicMock(return_value=mock_sock)
            mock_sock.__exit__ = MagicMock(return_value=False)
            with patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock):
                await proxy2._spawn_broker_if_needed()

        assert popen_count == 1, f"Expected 1 Popen call, got {popen_count}"

    @pytest.mark.asyncio
    async def test_lock_released_on_timeout(self, tmp_path: Path) -> None:
        """Lock file fd is closed (lock released) even when TimeoutError is raised."""
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.2)

        closed_fds: list[bool] = []
        real_open = open

        def tracking_open(path: object, mode: str = "r", **kwargs: object):  # type: ignore[override]
            f = real_open(path, mode, **kwargs)  # type: ignore[call-overload]
            real_close = f.close

            def close_tracking() -> None:
                closed_fds.append(True)
                real_close()

            f.close = close_tracking  # type: ignore[method-assign]
            return f

        with patch("builtins.open", tracking_open), patch("subprocess.Popen"), pytest.raises(
            TimeoutError
        ):
            await proxy._spawn_broker_if_needed()

        assert closed_fds, "Lock file was not closed after TimeoutError"


# ---------------------------------------------------------------------------
# Broker unavailable — JSON-RPC error response (P2-T4)
# ---------------------------------------------------------------------------


class TestBrokerProxyUnavailableError:
    @pytest.mark.asyncio
    async def test_connect_timeout_sends_jsonrpc_error(self, tmp_path: Path) -> None:
        """TimeoutError from _connect_with_timeout causes a JSON-RPC error to be written."""
        import json

        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()

        proxy = BrokerProxy(cfg, connect_timeout=0.1, stdout=stdout_writer)

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(side_effect=TimeoutError("timed out")),
        ):
            await proxy.run()  # must not raise

        assert stdout_writer.write.called
        raw = stdout_writer.write.call_args.args[0]
        response = json.loads(raw.decode())
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == -32001

    @pytest.mark.asyncio
    async def test_error_code_is_minus_32001(self, tmp_path: Path) -> None:
        """JSON-RPC error code is exactly -32001."""
        import json

        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()

        proxy = BrokerProxy(cfg, connect_timeout=0.1, stdout=stdout_writer)

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(side_effect=TimeoutError("test")),
        ):
            await proxy.run()

        raw = stdout_writer.write.call_args.args[0]
        response = json.loads(raw.decode())
        assert response["error"]["code"] == -32001

    @pytest.mark.asyncio
    async def test_error_message_includes_reason(self, tmp_path: Path) -> None:
        """Error message contains 'Broker unavailable:' prefix and the exception text."""
        import json

        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()

        proxy = BrokerProxy(cfg, connect_timeout=0.1, stdout=stdout_writer)

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(side_effect=TimeoutError("socket never appeared")),
        ):
            await proxy.run()

        raw = stdout_writer.write.call_args.args[0]
        response = json.loads(raw.decode())
        assert "Broker unavailable:" in response["error"]["message"]
        assert "socket never appeared" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_run_does_not_raise_on_connect_failure(self, tmp_path: Path) -> None:
        """run() returns cleanly (no exception) when broker is unavailable."""
        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()

        proxy = BrokerProxy(cfg, connect_timeout=0.1, stdout=stdout_writer)

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(side_effect=TimeoutError("unavailable")),
        ):
            # Must not raise
            await proxy.run()

    @pytest.mark.asyncio
    async def test_spawn_failure_sends_jsonrpc_error(self, tmp_path: Path) -> None:
        """TimeoutError from _spawn_broker_if_needed also triggers the JSON-RPC error response."""
        import json

        cfg = _make_config(tmp_path)
        stdout_writer = _make_writer()

        proxy = BrokerProxy(cfg, auto_spawn=True, connect_timeout=0.1, stdout=stdout_writer)

        with patch.object(
            proxy,
            "_spawn_broker_if_needed",
            AsyncMock(side_effect=TimeoutError("spawn timed out")),
        ):
            await proxy.run()

        assert stdout_writer.write.called
        raw = stdout_writer.write.call_args.args[0]
        response = json.loads(raw.decode())
        assert response["error"]["code"] == -32001
        assert "spawn timed out" in response["error"]["message"]


# ---------------------------------------------------------------------------
# Web UI mismatch warning (P2-T5)
# ---------------------------------------------------------------------------


class TestBrokerProxyWebUIMismatch:
    @pytest.mark.asyncio
    async def test_warning_printed_when_port_refused(self, tmp_path: Path) -> None:
        """Warns to stderr when web_ui_port set, existing broker found, but port not listening."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])
        sock_reader = _make_reader([])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            web_ui_port=19999,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        # Simulate a refused connection on the web UI port without making a real TCP connection.
        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect.side_effect = ConnectionRefusedError

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ), patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "sys.stderr"
        ) as mock_stderr:
            await proxy.run()

        # Warning must have been printed to stderr
        stderr_output = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        assert "Warning" in stderr_output
        assert "web-ui" in stderr_output.lower() or "--web-ui" in stderr_output

    @pytest.mark.asyncio
    async def test_no_warning_when_port_listening(self, tmp_path: Path) -> None:
        """No warning when the running broker's web UI port is accepting connections."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])
        sock_reader = _make_reader([])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            connect_timeout=0.1,
            web_ui_port=18888,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        # connect() does not raise → port is accepting → no warning

        with patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ), patch("mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock), patch(
            "sys.stderr"
        ) as mock_stderr:
            await proxy.run()

        stderr_output = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        assert "Warning" not in stderr_output

    @pytest.mark.asyncio
    async def test_no_warning_when_new_broker_spawned(self, tmp_path: Path) -> None:
        """No web UI mismatch probe when this proxy just spawned a fresh broker."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])
        sock_reader = _make_reader([])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        proxy = BrokerProxy(
            cfg,
            auto_spawn=True,
            connect_timeout=0.1,
            web_ui_port=19998,
            stdin=stdin_reader,
            stdout=stdout_writer,
        )

        async def fake_spawn() -> None:
            proxy._new_broker_spawned = True  # simulate that spawn happened

        with patch.object(proxy, "_spawn_broker_if_needed", fake_spawn), patch.object(
            proxy,
            "_connect_with_timeout",
            AsyncMock(return_value=(sock_reader, sock_writer)),
        ), patch("sys.stderr") as mock_stderr:
            await proxy.run()

        stderr_output = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        assert "Warning" not in stderr_output

    @pytest.mark.asyncio
    async def test_no_warning_when_web_ui_port_not_set(self, tmp_path: Path) -> None:
        """No probe or warning when web_ui_port is None (web UI not requested)."""
        cfg = _make_config(tmp_path)
        stdin_reader = _make_reader([])
        sock_reader = _make_reader([])
        sock_writer = _make_writer()
        stdout_writer = _make_writer()

        # web_ui_port not passed → defaults to None
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
        ), patch("sys.stderr") as mock_stderr:
            await proxy.run()

        stderr_output = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        assert "Warning" not in stderr_output

    def test_warning_is_actionable(self, tmp_path: Path) -> None:
        """Warning message tells user how to restart the broker."""
        cfg = _make_config(tmp_path)
        proxy = BrokerProxy(cfg, web_ui_port=19997)

        mock_sock = MagicMock()
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.connect.side_effect = OSError("connection refused")

        with patch("sys.stderr") as mock_stderr, patch(
            "mcpbridge_wrapper.broker.proxy.socket.socket", return_value=mock_sock
        ):
            proxy._warn_web_ui_mismatch()

        stderr_output = "".join(
            call.args[0] for call in mock_stderr.write.call_args_list if call.args
        )
        # Must mention the hint to restart/stop the broker
        assert "Warning" in stderr_output
        assert "broker.sock" in stderr_output or "Restart" in stderr_output


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

    def test_broker_flag_sets_spawn_and_connect(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker"])
        assert daemon is False
        assert connect is True
        assert spawn is True
        assert remaining == []

    def test_legacy_broker_connect_flag_is_forwarded(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-connect"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--broker-connect"]

    def test_legacy_broker_spawn_flag_is_forwarded(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--broker-spawn"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--broker-spawn"]

    def test_unknown_flags_pass_through(self) -> None:
        daemon, connect, spawn, remaining = _parse_broker_args(["--other-flag", "val"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--other-flag", "val"]

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
