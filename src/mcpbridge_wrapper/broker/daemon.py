"""Persistent broker daemon for mcpbridge-wrapper.

The BrokerDaemon owns a single ``xcrun mcpbridge`` upstream subprocess and
exposes readiness state to local MCP client proxies.  It handles:

- PID-file locking to prevent duplicate instances
- Stale-lock recovery (dead process leaves orphaned files behind)
- Exponential-backoff reconnection when the upstream crashes
- Graceful shutdown with configurable drain timeout

Lifecycle states
----------------
INIT → READY ↔ RECONNECTING → STOPPING → STOPPED

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md for the full
state-machine diagram and sequence diagrams.
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import json
import logging
import os
import signal
import sys
import threading
from asyncio.subprocess import PIPE
from typing import TYPE_CHECKING, Any

from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState

if TYPE_CHECKING:
    from mcpbridge_wrapper.broker.transport import UnixSocketServer

logger = logging.getLogger(__name__)


class BrokerDaemon:
    """Long-lived process that owns one upstream xcrun mcpbridge subprocess.

    Parameters
    ----------
    config:
        Configuration for socket path, PID file, upstream command, and
        timeout/backoff settings.
    """

    def __init__(
        self,
        config: BrokerConfig,
        transport: UnixSocketServer | None = None,
    ) -> None:
        """Initialise daemon with the given configuration.

        Parameters
        ----------
        config:
            Broker configuration.
        transport:
            Optional :class:`~mcpbridge_wrapper.broker.transport.UnixSocketServer`
            that will be started/stopped with this daemon and used to route
            upstream responses to connected clients.  If ``None``, upstream
            responses are parsed but not forwarded (useful for testing without
            a transport layer).
        """
        self._config = config
        self._transport = transport
        self._state = BrokerState.INIT
        self._upstream: asyncio.subprocess.Process | None = None
        self._read_task: asyncio.Task[None] | None = None
        self._reconnect_attempt: int = 0
        self._stop_event: asyncio.Event = asyncio.Event()
        self._stopped_event: asyncio.Event = asyncio.Event()
        # When set, run_forever should stop as soon as startup reaches READY.
        self._shutdown_requested: bool = False
        # Event loop running run_forever; used for thread-safe stop scheduling.
        self._loop: asyncio.AbstractEventLoop | None = None
        self._shutdown_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> BrokerState:
        """Current lifecycle state."""
        return self._state

    def status(self) -> dict[str, Any]:
        """Return a dictionary describing the current daemon status."""
        upstream_pid: int | None = None
        if self._upstream is not None:
            with contextlib.suppress(Exception):
                upstream_pid = self._upstream.pid
        return {
            "state": self._state.value,
            "pid": os.getpid(),
            "upstream_pid": upstream_pid,
        }

    def request_shutdown(self) -> None:
        """Request graceful daemon shutdown from any thread/context.

        This method is safe to call before :meth:`run_forever` starts. In that
        case the request is recorded and applied immediately after startup.
        """
        with self._shutdown_lock:
            self._shutdown_requested = True

        loop = self._loop
        if loop is None or not loop.is_running():
            return

        def _schedule_stop() -> None:
            # During startup (INIT), defer actual stop to run_forever() post-start check.
            if self._state == BrokerState.INIT:
                return
            asyncio.ensure_future(self.stop())

        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(_schedule_stop)

    async def start(self) -> None:
        """Start the broker: validate lock, launch upstream, then write PID file.

        The startup sequence is transactional: if any step after launching the
        upstream subprocess fails (PID file write, transport bind, etc.),
        :meth:`_rollback_startup` is invoked automatically to terminate the
        upstream, cancel the read task, remove stale files, and set the state
        to ``STOPPED``.  The original exception is always re-raised.

        Raises:
            RuntimeError: If another broker instance is already running (live PID found).
            OSError: If the transport cannot bind to the socket path, or another
                OS-level failure occurs during startup.
        """
        self._config.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Stale-lock / duplicate-instance check
        self._check_and_clear_stale_lock()

        # Launch upstream subprocess — failure here needs no rollback (nothing started yet)
        await self._launch_upstream()

        try:
            # Persist PID only after upstream launch succeeds.
            self._config.pid_file.write_text(str(os.getpid()))
            logger.debug("PID file written: %s", self._config.pid_file)

            # Background reader
            self._stop_event.clear()
            self._stopped_event.clear()
            self._read_task = asyncio.ensure_future(self._read_upstream_loop())

            # Start transport (Unix socket server) if provided — can raise OSError
            if self._transport is not None:
                await self._transport.start()

        except Exception:
            await self._rollback_startup()
            raise

        # Ensure socket/PID files are removed even on abnormal interpreter exit
        # (e.g. unhandled exception, sys.exit). SIGKILL cannot be intercepted.
        atexit.register(self._cleanup_files)

        self._state = BrokerState.READY
        logger.info(
            "Broker READY (upstream PID %s)",
            self._upstream.pid if self._upstream else "?",
        )

    async def stop(self) -> None:
        """Gracefully shut down the broker.

        Drains in-flight requests up to ``config.graceful_shutdown_timeout``
        seconds, then terminates the upstream subprocess and removes socket/PID.
        """
        if self._state == BrokerState.STOPPED:
            return
        if self._state == BrokerState.STOPPING:
            await self._stopped_event.wait()
            return

        self._state = BrokerState.STOPPING
        logger.info("Broker STOPPING")

        # Stop transport first so no new clients can connect / pending are drained
        if self._transport is not None:
            with contextlib.suppress(Exception):
                await self._transport.stop()

        # Signal read loop to exit
        self._stop_event.set()

        # Cancel background read task
        if self._read_task is not None and not self._read_task.done():
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                await asyncio.wait_for(
                    asyncio.shield(self._read_task),
                    timeout=self._config.graceful_shutdown_timeout,
                )

        try:
            # Terminate upstream
            if self._upstream is not None and self._upstream.returncode is None:
                with contextlib.suppress(Exception):
                    if self._upstream.stdin is not None:
                        self._upstream.stdin.close()
                try:
                    await asyncio.wait_for(
                        self._upstream.wait(),
                        timeout=self._config.graceful_shutdown_timeout,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Upstream did not exit cleanly; killing.")
                    self._upstream.kill()
                    await self._upstream.wait()
        finally:
            # Always mark shutdown complete so run_forever/stop waiters unblock.
            self._cleanup_files()
            self._state = BrokerState.STOPPED
            self._stopped_event.set()
            logger.info("Broker STOPPED")

    async def run_forever(self) -> None:
        """Start and block until a shutdown signal is received."""
        loop = asyncio.get_running_loop()
        self._loop = loop

        def _sync_signal_handler() -> None:
            self.request_shutdown()

        for sig in (signal.SIGTERM, signal.SIGINT):
            with contextlib.suppress(NotImplementedError, RuntimeError):
                loop.add_signal_handler(sig, _sync_signal_handler)

        try:
            await self.start()

            # Handle stop requests that happened before or during startup.
            if self._shutdown_requested:
                await self.stop()

            # Wait for shutdown to be requested and fully completed.
            await self._stop_event.wait()
            await self._stopped_event.wait()
        finally:
            self._loop = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _rollback_startup(self) -> None:
        """Roll back a failed :meth:`start` sequence.

        Called automatically when any step after ``_launch_upstream`` raises an
        exception.  Cancels the background read task (if started), terminates
        the upstream subprocess (if running), removes PID/socket files, and
        sets the daemon state to ``STOPPED``.

        Safe to call even if the upstream was never launched (idempotent).
        """
        logger.warning("Rolling back failed broker startup.")

        # Cancel background read task if it was already started
        if self._read_task is not None and not self._read_task.done():
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._read_task
        self._read_task = None

        # Terminate the upstream subprocess
        if self._upstream is not None and self._upstream.returncode is None:
            with contextlib.suppress(Exception):
                self._upstream.terminate()
            try:
                await asyncio.wait_for(
                    self._upstream.wait(),
                    timeout=self._config.graceful_shutdown_timeout,
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(Exception):
                    self._upstream.kill()
                with contextlib.suppress(Exception):
                    await self._upstream.wait()
        self._upstream = None

        # Remove stale files and mark daemon as stopped
        self._cleanup_files()
        self._state = BrokerState.STOPPED
        # Keep event flags consistent with STOPPED state for future callers.
        self._stop_event.set()
        self._stopped_event.set()
        logger.info("Startup rollback complete — broker STOPPED.")

    def _check_and_clear_stale_lock(self) -> None:
        """Check for a stale or live PID file and handle accordingly.

        Raises:
            RuntimeError: If a live broker process is already running.
        """
        pid_file = self._config.pid_file
        sock_file = self._config.socket_path

        if not pid_file.exists():
            # No lock file — clear any orphaned socket and proceed
            if sock_file.exists():
                sock_file.unlink(missing_ok=True)
            return

        raw = pid_file.read_text().strip()
        try:
            pid = int(raw)
        except ValueError:
            logger.warning("Corrupt PID file (%r); removing.", raw)
            pid_file.unlink(missing_ok=True)
            sock_file.unlink(missing_ok=True)
            return

        try:
            os.kill(pid, 0)
            # Process is alive → refuse to start
            raise RuntimeError(
                f"Broker already running (PID {pid}). "
                "Stop it first or remove the PID file manually."
            )
        except ProcessLookupError:
            # Process is dead → stale lock
            logger.info("Stale lock found (PID %d dead); cleaning up.", pid)
            pid_file.unlink(missing_ok=True)
            sock_file.unlink(missing_ok=True)
        except PermissionError as err:
            # Process exists but owned by another user — treat as running
            raise RuntimeError(
                f"Broker appears to be running under a different user (PID {pid})."
            ) from err

    async def _launch_upstream(self) -> None:
        """Launch or re-launch the upstream bridge subprocess."""
        self._upstream = await asyncio.create_subprocess_exec(
            *self._config.upstream_cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=sys.stderr,
        )
        logger.debug("Upstream launched (PID %d)", self._upstream.pid)

    async def _read_upstream_loop(self) -> None:
        """Read JSON-RPC lines from upstream stdout indefinitely.

        When EOF is received and the daemon is not stopping, triggers
        reconnection with exponential backoff.
        """
        while not self._stop_event.is_set():
            if self._upstream is None or self._upstream.stdout is None:
                await asyncio.sleep(0.05)
                continue

            try:
                raw = await self._upstream.stdout.readline()
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception as exc:
                logger.warning("Upstream read error: %s", exc)
                raw = b""

            if not raw:
                # EOF
                if self._stop_event.is_set() or self._state == BrokerState.STOPPING:
                    break
                logger.warning("Upstream EOF detected; scheduling reconnect.")
                await self._reconnect()
                continue

            # Decode, log, and route to connected clients
            try:
                line = raw.decode() if isinstance(raw, bytes) else raw
                line = line.rstrip("\n")
                logger.debug("Upstream → broker: %s", line)
                if self._transport is not None:
                    await self._transport.route_upstream_response(line)
                else:
                    # Validate JSON even without a transport
                    json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.debug("Non-JSON upstream output (%s): %r", exc, raw)

    async def _reconnect(self) -> None:
        """Attempt to relaunch the upstream with exponential backoff."""
        self._state = BrokerState.RECONNECTING
        cap = self._config.reconnect_backoff_cap

        while not self._stop_event.is_set():
            delay = min(2**self._reconnect_attempt, cap)
            logger.info(
                "Reconnect attempt %d in %ds…",
                self._reconnect_attempt,
                delay,
            )
            if delay > 0:
                await asyncio.sleep(delay)

            if self._stop_event.is_set():
                break

            try:
                await self._launch_upstream()
                self._reconnect_attempt = 0
                self._state = BrokerState.READY
                logger.info(
                    "Upstream reconnected (PID %d)",
                    self._upstream.pid if self._upstream else -1,
                )
                return
            except OSError as exc:
                logger.error("Failed to launch upstream: %s", exc)
                self._reconnect_attempt += 1

        # Stop event set during reconnect
        self._state = BrokerState.STOPPING

    def _cleanup_files(self) -> None:
        """Remove PID file and socket file."""
        for path in (self._config.pid_file, self._config.socket_path):
            try:
                path.unlink(missing_ok=True)
                logger.debug("Removed %s", path)
            except Exception as exc:
                logger.warning("Could not remove %s: %s", path, exc)
