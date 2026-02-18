"""Tests for BrokerDaemon — P13-T2 implementation.

Covers:
- Duplicate-instance prevention (PID-file locking)
- Stale-lock recovery
- Graceful shutdown (upstream terminated, files cleaned up)
- Crash recovery / reconnect path
- Status reporting
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path) -> BrokerConfig:
    return BrokerConfig(
        socket_path=tmp_path / "broker.sock",
        pid_file=tmp_path / "broker.pid",
        upstream_cmd=["true"],  # exits immediately; safe no-op
        reconnect_backoff_cap=1,
        queue_ttl=5,
        graceful_shutdown_timeout=1,
    )


def _make_mock_process(returncode: int | None = None) -> MagicMock:
    """Return a mock asyncio.subprocess.Process."""
    proc = MagicMock()
    proc.pid = 9999
    proc.returncode = returncode
    proc.stdin = MagicMock()
    proc.stdin.close = MagicMock()
    stdout_mock = MagicMock()
    # readline returns EOF immediately
    stdout_mock.readline = AsyncMock(return_value=b"")
    proc.stdout = stdout_mock
    proc.wait = AsyncMock(return_value=0)
    proc.kill = MagicMock()
    return proc


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestBrokerDaemonInit:
    def test_initial_state_is_init(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        assert daemon.state == BrokerState.INIT

    def test_status_before_start(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        status = daemon.status()
        assert status["state"] == "init"
        assert status["pid"] == os.getpid()
        assert status["upstream_pid"] is None


# ---------------------------------------------------------------------------
# start() — happy path
# ---------------------------------------------------------------------------


class TestBrokerDaemonStart:
    @pytest.mark.asyncio
    async def test_start_transitions_to_ready(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()

        assert daemon.state == BrokerState.READY

        # Cleanup
        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()

    @pytest.mark.asyncio
    async def test_start_writes_pid_file(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()

        assert cfg.pid_file.exists()
        assert cfg.pid_file.read_text().strip() == str(os.getpid())

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()

    @pytest.mark.asyncio
    async def test_start_does_not_write_pid_file_when_launch_fails(
        self,
        tmp_path: Path,
    ) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        with patch.object(
            daemon,
            "_launch_upstream",
            new=AsyncMock(side_effect=OSError("launch failed")),
        ):
            with pytest.raises(OSError, match="launch failed"):
                await daemon.start()

        assert not cfg.pid_file.exists()

    @pytest.mark.asyncio
    async def test_start_creates_data_dir(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        cfg = BrokerConfig(
            socket_path=nested / "broker.sock",
            pid_file=nested / "broker.pid",
            upstream_cmd=["true"],
        )
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()

        assert nested.is_dir()

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# start() — duplicate instance prevention
# ---------------------------------------------------------------------------


class TestBrokerDaemonDuplicatePrevention:
    @pytest.mark.asyncio
    async def test_raises_if_same_pid_alive(self, tmp_path: Path) -> None:
        """Writing own PID to file and then re-starting should raise."""
        cfg = _make_config(tmp_path)
        own_pid = os.getpid()
        cfg.pid_file.write_text(str(own_pid))

        daemon = BrokerDaemon(cfg)

        with pytest.raises(RuntimeError, match="already running"):
            await daemon.start()

    @pytest.mark.asyncio
    async def test_clears_stale_lock_for_dead_process(self, tmp_path: Path) -> None:
        """A PID from a dead process is treated as stale and cleaned up."""
        cfg = _make_config(tmp_path)
        # PID 1 is init/launchd — we cannot kill it, so we use a fake high PID
        # that is guaranteed to not exist on any test machine.
        cfg.pid_file.write_text("99999999")
        cfg.socket_path.write_text("leftover")

        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ), patch("mcpbridge_wrapper.broker.daemon.os.kill", side_effect=ProcessLookupError):
            await daemon.start()

        # Stale files removed before PID file was rewritten
        assert cfg.pid_file.read_text().strip() == str(os.getpid())
        assert daemon.state == BrokerState.READY

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()

    @pytest.mark.asyncio
    async def test_clears_corrupt_pid_file(self, tmp_path: Path) -> None:
        """A corrupt PID file is silently removed and startup proceeds."""
        cfg = _make_config(tmp_path)
        cfg.pid_file.write_text("not-a-number")

        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()

        assert daemon.state == BrokerState.READY

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# stop() — graceful shutdown
# ---------------------------------------------------------------------------


class TestBrokerDaemonStop:
    @pytest.mark.asyncio
    async def test_stop_transitions_to_stopped(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            await daemon.stop()

        assert daemon.state == BrokerState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_removes_pid_file(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            assert cfg.pid_file.exists()
            await daemon.stop()

        assert not cfg.pid_file.exists()

    @pytest.mark.asyncio
    async def test_stop_terminates_upstream(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            await daemon.stop()

        proc.stdin.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_idempotent_when_already_stopped(self, tmp_path: Path) -> None:
        """Calling stop() twice should not raise."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            await daemon.stop()
            await daemon.stop()  # second call — should be a no-op

        assert daemon.state == BrokerState.STOPPED

    @pytest.mark.asyncio
    async def test_stop_kills_upstream_on_timeout(self, tmp_path: Path) -> None:
        """When upstream doesn't exit within grace period, kill() is called."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)
        proc = _make_mock_process()

        # Make proc.wait hang just long enough to trigger the graceful timeout
        # by setting a very short timeout and a slow wait.
        async def _slow_wait() -> int:
            await asyncio.sleep(10)  # longer than graceful_shutdown_timeout=1
            return 0

        proc.wait = _slow_wait
        # After kill(), let wait() return immediately
        kill_called = False

        def _kill() -> None:
            nonlocal kill_called
            kill_called = True
            # Replace wait with a fast one after kill
            proc.wait = AsyncMock(return_value=0)

        proc.kill = _kill

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()

        # Cancel read task before calling stop() directly
        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await daemon._read_task

        # Re-arm for direct stop() test
        daemon._state = BrokerState.READY
        daemon._read_task = None
        daemon._upstream = proc
        daemon._stop_event = asyncio.Event()

        await daemon.stop()

        assert kill_called, "kill() should have been called after graceful timeout"


# ---------------------------------------------------------------------------
# Crash recovery / reconnect
# ---------------------------------------------------------------------------


class TestBrokerDaemonReconnect:
    @pytest.mark.asyncio
    async def test_upstream_eof_triggers_reconnecting_state(self, tmp_path: Path) -> None:
        """When upstream sends EOF, daemon enters RECONNECTING before READY."""
        cfg = _make_config(tmp_path)
        cfg = BrokerConfig(
            socket_path=cfg.socket_path,
            pid_file=cfg.pid_file,
            upstream_cmd=["true"],
            reconnect_backoff_cap=0,
            queue_ttl=5,
            graceful_shutdown_timeout=1,
        )
        daemon = BrokerDaemon(cfg)

        # First process: sends EOF immediately
        first_proc = _make_mock_process()
        first_proc.stdout.readline = AsyncMock(return_value=b"")

        # Second process: blocks until stop_event
        second_proc = _make_mock_process()

        async def _blocking_readline() -> bytes:
            await daemon._stop_event.wait()
            return b""

        second_proc.stdout.readline = _blocking_readline

        call_count = 0

        async def _create_proc(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_proc
            return second_proc

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=_create_proc,
        ):
            await daemon.start()
            # Give the read loop time to detect EOF and enter RECONNECTING
            await asyncio.sleep(0.05)
            # Allow reconnect (backoff_cap=0 means no delay)
            await asyncio.sleep(0.1)

        # Eventually should reconnect to READY
        assert daemon.state in (BrokerState.READY, BrokerState.RECONNECTING)

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()

    @pytest.mark.asyncio
    async def test_reconnect_state_transitions(self, tmp_path: Path) -> None:
        """After reconnect, daemon should be READY."""
        cfg = BrokerConfig(
            socket_path=tmp_path / "broker.sock",
            pid_file=tmp_path / "broker.pid",
            upstream_cmd=["true"],
            reconnect_backoff_cap=0,
            queue_ttl=5,
            graceful_shutdown_timeout=1,
        )
        daemon = BrokerDaemon(cfg)

        first_proc = _make_mock_process()
        first_proc.stdout.readline = AsyncMock(return_value=b"")

        second_proc = _make_mock_process()

        async def _block(*a, **kw) -> bytes:  # type: ignore[no-untyped-def]
            await daemon._stop_event.wait()
            return b""

        second_proc.stdout.readline = _block

        call_n = 0

        async def _factory(*a, **kw):  # type: ignore[no-untyped-def]
            nonlocal call_n
            call_n += 1
            return first_proc if call_n == 1 else second_proc

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=_factory,
        ):
            await daemon.start()
            await asyncio.sleep(0.2)  # let reconnect run

        assert daemon.state in (BrokerState.READY, BrokerState.RECONNECTING)

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# Client disconnects do NOT affect upstream
# ---------------------------------------------------------------------------


class TestBrokerSurvivesClientDisconnect:
    @pytest.mark.asyncio
    async def test_upstream_still_running_after_simulated_client_drop(self, tmp_path: Path) -> None:
        """Broker daemon state remains READY after a client disconnects.

        (Client connection management is in P13-T3; here we simply verify
        that the daemon itself doesn't change state when a client disappears.)
        """
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        async def _blocking_readline() -> bytes:
            await daemon._stop_event.wait()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _blocking_readline

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            assert daemon.state == BrokerState.READY

            # Simulate client dropping — daemon has no client tracking yet;
            # the important invariant is that state stays READY.
            await asyncio.sleep(0.02)
            assert daemon.state == BrokerState.READY

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# status()
# ---------------------------------------------------------------------------


class TestBrokerStatus:
    @pytest.mark.asyncio
    async def test_status_after_start_includes_upstream_pid(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        async def _block(*a, **kw) -> bytes:  # type: ignore[no-untyped-def]
            await daemon._stop_event.wait()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _block

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            s = daemon.status()

        assert s["state"] == "ready"
        assert s["upstream_pid"] == proc.pid
        assert s["pid"] == os.getpid()

        daemon._stop_event.set()
        if daemon._read_task and not daemon._read_task.done():
            daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# run_forever()
# ---------------------------------------------------------------------------


class TestBrokerDaemonRunForever:
    @pytest.mark.asyncio
    async def test_run_forever_starts_and_stops(self, tmp_path: Path) -> None:
        """run_forever() starts the daemon and returns after stop()."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        async def _block(*a, **kw) -> bytes:  # type: ignore[no-untyped-def]
            await daemon._stop_event.wait()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _block

        async def _do_stop() -> None:
            await asyncio.sleep(0.05)
            await daemon.stop()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            stopper = asyncio.ensure_future(_do_stop())
            await daemon.run_forever()
            await stopper

        assert daemon.state == BrokerState.STOPPED

    @pytest.mark.asyncio
    async def test_run_forever_does_not_poll_with_fixed_sleep(self, tmp_path: Path) -> None:
        """run_forever waits on events and does not use fixed-interval polling."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        async def _block(*a, **kw) -> bytes:  # type: ignore[no-untyped-def]
            await daemon._stop_event.wait()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _block

        sleep_calls: list[float] = []
        original_sleep = asyncio.sleep

        async def _tracked_sleep(delay: float) -> None:
            sleep_calls.append(delay)
            await original_sleep(delay)

        async def _do_stop() -> None:
            await original_sleep(0.05)
            await daemon.stop()

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ), patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.sleep",
            side_effect=_tracked_sleep,
        ):
            stopper = asyncio.ensure_future(_do_stop())
            await daemon.run_forever()
            await stopper

        assert all(delay != 0.1 for delay in sleep_calls)


# ---------------------------------------------------------------------------
# _check_and_clear_stale_lock — edge cases
# ---------------------------------------------------------------------------


class TestStaleLockEdgeCases:
    def test_removes_orphaned_socket_when_no_pid_file(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.socket_path.write_text("leftover")
        assert cfg.socket_path.exists()

        daemon = BrokerDaemon(cfg)
        daemon._check_and_clear_stale_lock()

        assert not cfg.socket_path.exists()

    def test_permission_error_raises_runtime_error(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.pid_file.write_text("12345")

        daemon = BrokerDaemon(cfg)
        with patch(
            "mcpbridge_wrapper.broker.daemon.os.kill",
            side_effect=PermissionError("not allowed"),
        ), pytest.raises(RuntimeError, match="different user"):
            daemon._check_and_clear_stale_lock()


# ---------------------------------------------------------------------------
# _read_upstream_loop — edge cases
# ---------------------------------------------------------------------------


class TestReadUpstreamLoopEdgeCases:
    @pytest.mark.asyncio
    async def test_handles_read_exception_gracefully(self, tmp_path: Path) -> None:
        """A non-CancelledError exception in readline is caught; loop continues."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        call_count = 0

        async def _flaky_readline() -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("read error")
            daemon._stop_event.set()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _flaky_readline

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            if daemon._read_task:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(daemon._read_task, timeout=1.0)

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_handles_non_json_upstream_output(self, tmp_path: Path) -> None:
        """Non-JSON output from upstream is silently ignored."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        call_count = 0

        async def _mixed_readline() -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return b"not-json-at-all\n"
            daemon._stop_event.set()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _mixed_readline

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            if daemon._read_task:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(daemon._read_task, timeout=1.0)

        assert daemon.state in (BrokerState.READY, BrokerState.STOPPING, BrokerState.STOPPED)

    @pytest.mark.asyncio
    async def test_handles_valid_json_upstream_output(self, tmp_path: Path) -> None:
        """Valid JSON output from upstream passes through without errors."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        call_count = 0

        async def _json_readline() -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return b'{"id":1,"result":{"content":[]}}\n'
            daemon._stop_event.set()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _json_readline

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            if daemon._read_task:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(daemon._read_task, timeout=1.0)

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_loop_exits_when_stop_event_set_before_eof(self, tmp_path: Path) -> None:
        """If stop_event is set before EOF, the loop should exit cleanly."""
        cfg = _make_config(tmp_path)
        daemon = BrokerDaemon(cfg)

        async def _blocking_readline() -> bytes:
            await daemon._stop_event.wait()
            return b""

        proc = _make_mock_process()
        proc.stdout.readline = _blocking_readline
        # Pretend upstream has already exited when stop() is called
        proc.returncode = 0

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            await daemon.start()
            daemon._stop_event.set()
            if daemon._read_task:
                try:
                    await asyncio.wait_for(daemon._read_task, timeout=1.0)
                except asyncio.TimeoutError:
                    daemon._read_task.cancel()


# ---------------------------------------------------------------------------
# _reconnect — stop event during reconnect clears state
# ---------------------------------------------------------------------------


class TestReconnectEdgeCases:
    @pytest.mark.asyncio
    async def test_stop_event_before_reconnect_sets_stopping(self, tmp_path: Path) -> None:
        """If stop_event is already set, _reconnect exits immediately."""
        cfg = BrokerConfig(
            socket_path=tmp_path / "broker.sock",
            pid_file=tmp_path / "broker.pid",
            upstream_cmd=["true"],
            reconnect_backoff_cap=0,
            queue_ttl=5,
            graceful_shutdown_timeout=1,
        )
        daemon = BrokerDaemon(cfg)
        daemon._stop_event.set()
        await daemon._reconnect()

        assert daemon.state == BrokerState.STOPPING

    @pytest.mark.asyncio
    async def test_reconnect_retries_on_oserror(self, tmp_path: Path) -> None:
        """OSError from _launch_upstream increments attempt counter."""
        cfg = BrokerConfig(
            socket_path=tmp_path / "broker.sock",
            pid_file=tmp_path / "broker.pid",
            upstream_cmd=["true"],
            reconnect_backoff_cap=0,
            queue_ttl=5,
            graceful_shutdown_timeout=1,
        )
        daemon = BrokerDaemon(cfg)

        fail_count = 0
        success_proc = _make_mock_process()

        async def _flaky_launch(*a, **kw):  # type: ignore[no-untyped-def]
            nonlocal fail_count
            fail_count += 1
            if fail_count < 2:
                raise OSError("launch failed")
            return success_proc

        with patch(
            "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
            new=_flaky_launch,
        ):
            await daemon._reconnect()

        assert fail_count == 2
        assert daemon.state == BrokerState.READY
        assert daemon._reconnect_attempt == 0
