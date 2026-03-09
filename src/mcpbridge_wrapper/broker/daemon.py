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

from mcpbridge_wrapper import __version__
from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState

if TYPE_CHECKING:
    from mcpbridge_wrapper.broker.transport import UnixSocketServer

logger = logging.getLogger(__name__)

# Reserved JSON-RPC IDs for broker-internal probes.
# Valid broker_ids are (session_id << 20) where session_id ≥ 1, so the minimum
# broker_id is 1_048_576.  These negative/zero values can never collide.
_BROKER_INIT_ID = 0
_BROKER_TOOLS_ID = -1
_TOOLS_PROBE_RETRY_BASE_DELAY_SECONDS = 0.25
_TOOLS_PROBE_RETRY_MAX_DELAY_SECONDS = 2.0


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
        # Set after the broker's own initialize probe succeeds; cleared on reconnect.
        self._upstream_initialized: asyncio.Event = asyncio.Event()
        # Cached tools/list result (JSON string); None until first successful probe.
        self._tools_list_cache: str | None = None
        # Set once a usable tools/list response has been cached for clients.
        self._tools_catalog_ready: asyncio.Event = asyncio.Event()
        # Background retry task for broker-internal tools/list warm-up probes.
        self._tools_probe_retry_task: asyncio.Task[None] | None = None
        self._tools_probe_retry_attempt: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> BrokerState:
        """Current lifecycle state."""
        return self._state

    @property
    def upstream_initialized(self) -> asyncio.Event:
        """Event that is set once the upstream has completed an initialize round-trip.

        Cleared at the start of each reconnect attempt and re-set when the probe
        response arrives.  Transport clients gate on this event before forwarding
        requests so that no empty ``tools/list`` responses are served during the
        Xcode approval window or other upstream restart scenarios.
        """
        return self._upstream_initialized

    @property
    def tools_catalog_ready(self) -> asyncio.Event:
        """Event that is set once a non-empty cached ``tools/list`` result exists."""
        return self._tools_catalog_ready

    def status(self) -> dict[str, Any]:
        """Return a dictionary describing the current daemon status."""
        upstream_pid: int | None = None
        upstream_alive = False
        if self._upstream is not None:
            with contextlib.suppress(Exception):
                upstream_pid = self._upstream.pid
            with contextlib.suppress(Exception):
                upstream_alive = self._upstream.returncode is None

        connected_clients = 0
        if self._transport is not None:
            with contextlib.suppress(Exception):
                connected_clients = len(self._transport.sessions)

        return {
            "state": self._state.value,
            "pid": os.getpid(),
            "upstream_pid": upstream_pid,
            "upstream_alive": upstream_alive,
            "upstream_initialized": self._upstream_initialized.is_set(),
            "tools_list_cached": self._tools_list_cache is not None,
            "connected_clients": connected_clients,
            "reconnect_attempt": self._reconnect_attempt,
            "shutdown_requested": self._shutdown_requested,
            "socket_path": str(self._config.socket_path),
            "pid_file": str(self._config.pid_file),
            "version_file": str(self._config.version_file),
            "version": __version__,
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
        # Send the broker-internal initialize probe so the read loop can set
        # _upstream_initialized once the upstream responds.
        await self._send_broker_probes()

        try:
            # Persist PID only after upstream launch succeeds.
            self._config.pid_file.write_text(str(os.getpid()))
            logger.debug("PID file written: %s", self._config.pid_file)

            # Write version stamp so proxy clients can detect version mismatches.
            self._config.version_file.write_text(__version__)
            logger.debug("Version file written: %s", self._config.version_file)

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
        self._cancel_tools_probe_retry()

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

    async def _send_broker_probes(self) -> None:
        """Send the broker-internal ``initialize`` probe to the upstream.

        Uses the reserved ID :data:`_BROKER_INIT_ID` (0) so the response can be
        intercepted in :meth:`_read_upstream_loop` without being routed to any
        client.  After the response arrives, the read loop automatically sends the
        ``tools/list`` probe (id :data:`_BROKER_TOOLS_ID`) and caches the result.

        This coroutine returns immediately after writing to stdin; the response is
        handled asynchronously by the read loop.
        """
        upstream = self._upstream
        if upstream is None or upstream.stdin is None:
            logger.warning("_send_broker_probes called with no upstream stdin; skipping.")
            return
        probe = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": _BROKER_INIT_ID,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcpbridge-broker", "version": __version__},
                },
            },
            separators=(",", ":"),
        )
        try:
            upstream.stdin.write((probe + "\n").encode())
            await upstream.stdin.drain()
            logger.debug("Broker initialize probe sent (id=%d)", _BROKER_INIT_ID)
        except Exception as exc:
            logger.warning("Failed to send broker initialize probe: %s", exc)

    async def _send_tools_list_probe(self) -> None:
        """Send the broker-internal ``tools/list`` probe to the upstream."""
        upstream = self._upstream
        if upstream is None or upstream.stdin is None:
            logger.warning("Failed to send tools/list probe: no upstream stdin available.")
            return

        tools_probe = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": _BROKER_TOOLS_ID,
                "method": "tools/list",
                "params": {},
            },
            separators=(",", ":"),
        )
        try:
            upstream.stdin.write((tools_probe + "\n").encode())
            await upstream.stdin.drain()
            logger.debug("Broker tools/list probe sent (id=%d)", _BROKER_TOOLS_ID)
        except Exception as exc:
            logger.warning("Failed to send tools/list probe: %s", exc)

    async def _retry_tools_list_probe_after_delay(self, delay: float) -> None:
        """Retry broker warm-up probing after a short delay."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            if self._stop_event.is_set():
                return
            await self._send_tools_list_probe()
        except asyncio.CancelledError:
            raise
        finally:
            if asyncio.current_task() is self._tools_probe_retry_task:
                self._tools_probe_retry_task = None

    def _schedule_tools_list_probe(self, *, delay: float = 0.0) -> None:
        """Ensure a broker-internal ``tools/list`` probe is scheduled."""
        if self._stop_event.is_set():
            return
        task = self._tools_probe_retry_task
        if task is not None and not task.done():
            return
        self._tools_probe_retry_task = asyncio.create_task(
            self._retry_tools_list_probe_after_delay(delay)
        )

    def _reset_tools_probe_retry_backoff(self) -> None:
        """Reset retry state for broker-internal tools/list warm-up probing."""
        self._tools_probe_retry_attempt = 0

    def _next_tools_probe_retry_delay(self) -> float:
        """Return the next bounded backoff delay for broker tools/list retries."""
        delay = min(
            _TOOLS_PROBE_RETRY_BASE_DELAY_SECONDS * (2**self._tools_probe_retry_attempt),
            _TOOLS_PROBE_RETRY_MAX_DELAY_SECONDS,
        )
        self._tools_probe_retry_attempt += 1
        return float(delay)

    def _cancel_tools_probe_retry(self) -> None:
        """Cancel any pending retry for the broker-internal tools/list probe."""
        task = self._tools_probe_retry_task
        if task is not None and not task.done():
            task.cancel()
        self._tools_probe_retry_task = None
        self._reset_tools_probe_retry_backoff()

    async def _rollback_startup(self) -> None:
        """Roll back a failed :meth:`start` sequence.

        Called automatically when any step after ``_launch_upstream`` raises an
        exception.  Cancels the background read task (if started), terminates
        the upstream subprocess (if running), removes PID/socket files, and
        sets the daemon state to ``STOPPED``.

        Safe to call even if the upstream was never launched (idempotent).
        """
        logger.warning("Rolling back failed broker startup.")
        self._cancel_tools_probe_retry()

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
        ver_file = self._config.version_file

        if not pid_file.exists():
            # No lock file — clear any orphaned socket/version and proceed
            if sock_file.exists():
                sock_file.unlink(missing_ok=True)
            ver_file.unlink(missing_ok=True)
            return

        raw = pid_file.read_text().strip()
        try:
            pid = int(raw)
        except ValueError:
            logger.warning("Corrupt PID file (%r); removing.", raw)
            pid_file.unlink(missing_ok=True)
            sock_file.unlink(missing_ok=True)
            ver_file.unlink(missing_ok=True)
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
            ver_file.unlink(missing_ok=True)
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

                # Intercept broker-internal probe responses before routing.
                msg = json.loads(line)
                raw_id = msg.get("id") if isinstance(msg, dict) else None

                if raw_id == _BROKER_INIT_ID:
                    # Broker's own initialize probe response received.
                    self._upstream_initialized.set()
                    logger.info("Upstream initialize probe acknowledged; upstream is ready.")
                    upstream = self._upstream
                    if upstream is not None and upstream.stdin is not None:
                        # Complete the MCP handshake: send notifications/initialized so
                        # the upstream considers the session fully open before we issue
                        # any further requests.  Without this, xcrun mcpbridge queues
                        # all subsequent messages (including tools/list) indefinitely.
                        initialized_notif = json.dumps(
                            {"jsonrpc": "2.0", "method": "notifications/initialized"},
                            separators=(",", ":"),
                        )
                        try:
                            upstream.stdin.write((initialized_notif + "\n").encode())
                            await upstream.stdin.drain()
                            logger.debug("Broker notifications/initialized sent")
                        except Exception as exc:
                            logger.warning("Failed to send notifications/initialized: %s", exc)
                    # Now fetch tools/list for the cache.
                    upstream = self._upstream
                    if upstream is not None and upstream.stdin is not None:
                        self._reset_tools_probe_retry_backoff()
                        self._schedule_tools_list_probe()
                    continue

                if raw_id == _BROKER_TOOLS_ID:
                    # Broker's own tools/list probe response received — cache it.
                    if isinstance(msg, dict) and "result" in msg:
                        result = msg.get("result")
                        tools = result.get("tools") if isinstance(result, dict) else None
                        if isinstance(tools, list) and tools:
                            self._cancel_tools_probe_retry()
                            self._tools_list_cache = line
                            self._tools_catalog_ready.set()
                            logger.info(
                                "tools/list cache populated with %d tool(s) (%d bytes).",
                                len(tools),
                                len(line),
                            )
                        else:
                            self._tools_list_cache = None
                            self._tools_catalog_ready.clear()
                            delay = self._next_tools_probe_retry_delay()
                            log_fn = (
                                logger.warning
                                if self._tools_probe_retry_attempt == 1
                                else logger.debug
                            )
                            log_fn(
                                "Broker tools/list probe returned an empty or invalid "
                                "tool catalog; retry %d in %.2fs.",
                                self._tools_probe_retry_attempt,
                                delay,
                            )
                            self._schedule_tools_list_probe(delay=delay)
                    else:
                        self._tools_list_cache = None
                        self._tools_catalog_ready.clear()
                        delay = self._next_tools_probe_retry_delay()
                        log_fn = (
                            logger.warning if self._tools_probe_retry_attempt == 1 else logger.debug
                        )
                        log_fn(
                            "Broker tools/list probe returned no result; retry %d in %.2fs.",
                            self._tools_probe_retry_attempt,
                            delay,
                        )
                        self._schedule_tools_list_probe(delay=delay)
                    continue

                if self._transport is not None:
                    await self._transport.route_upstream_response(line)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.debug("Non-JSON upstream output (%s): %r", exc, raw)

    async def _reconnect(self) -> None:
        """Attempt to relaunch the upstream with exponential backoff."""
        self._state = BrokerState.RECONNECTING
        # Invalidate readiness gate and cache so clients wait for the new upstream.
        self._upstream_initialized.clear()
        self._tools_list_cache = None
        self._tools_catalog_ready.clear()
        self._cancel_tools_probe_retry()
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
                await self._send_broker_probes()
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
        """Remove PID file, socket file, and version file."""
        for path in (self._config.pid_file, self._config.socket_path, self._config.version_file):
            try:
                path.unlink(missing_ok=True)
                logger.debug("Removed %s", path)
            except Exception as exc:
                logger.warning("Could not remove %s: %s", path, exc)
