"""Client proxy mode for the persistent broker.

The BrokerProxy is the short-lived per-MCP-client process.  It connects to
the broker's Unix domain socket and bridges the MCP client's stdio transport
to the broker, forwarding JSON-RPC messages in both directions.

This allows existing MCP clients configured for stdio to transparently
use the persistent broker without any client-side changes beyond their
command configuration (adding ``--broker`` flag).

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md §3.7 for the
sequence diagram of the proxy connect/disconnect lifecycle.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time

from mcpbridge_wrapper import __version__
from mcpbridge_wrapper.broker.types import BrokerConfig

logger = logging.getLogger(__name__)


class BrokerProxy:
    """Forwards stdio ↔ Unix socket for a single MCP client.

    Parameters
    ----------
    config:
        Shared broker configuration (socket path, PID file, upstream cmd).
    auto_spawn:
        When ``True``, attempt to spawn the broker daemon if the socket is
        absent before connecting. Corresponds to the ``--broker`` CLI flag.
    connect_timeout:
        Maximum seconds to wait for the broker socket to become available.
    web_ui_port:
        When set, the proxy checks whether the running broker exposes a web UI
        on this port after connecting to an existing daemon.  If the port is
        not accepting connections, a warning is printed to stderr explaining
        how to restart the broker with ``--web-ui``.
    stdin:
        Asyncio stream to read from (defaults to ``sys.stdin.buffer``).
    stdout:
        Asyncio stream to write to (defaults to ``sys.stdout.buffer``).
    """

    def __init__(
        self,
        config: BrokerConfig,
        *,
        auto_spawn: bool = False,
        connect_timeout: float = 10.0,
        spawn_args: list[str] | None = None,
        web_ui_port: int | None = None,
        stdin: asyncio.StreamReader | None = None,
        stdout: asyncio.StreamWriter | None = None,
    ) -> None:
        """Initialise the proxy with the given broker configuration."""
        self._config = config
        self._auto_spawn = auto_spawn
        self._connect_timeout = connect_timeout
        # Spawn command args for the daemon process (without interpreter/module prefix).
        # Defaults to plain broker daemon mode.
        self._spawn_args = list(spawn_args) if spawn_args else ["--broker-daemon"]
        self._web_ui_port = web_ui_port
        # Set to True when this proxy spawns a fresh broker daemon, so the
        # web-UI mismatch probe is skipped (new daemon may not have HTTP ready yet).
        self._new_broker_spawned: bool = False
        self._stdin = stdin
        self._stdout = stdout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Connect to broker and forward stdio until client disconnects.

        Lifecycle
        ---------
        1. Optionally spawn broker if ``auto_spawn`` and socket absent.
        2. Connect to broker Unix socket (with timeout).
        3. Run bidirectional forward until stdin EOF or socket EOF.
        4. Close socket gracefully — broker process is **not** signalled.

        If the broker is unavailable (timeout, refused, spawn failure), a
        JSON-RPC ``-32001`` error response is written to stdout so the MCP
        client receives a meaningful error instead of silently hanging.
        """
        try:
            if self._auto_spawn:
                await self._spawn_broker_if_needed()

            sock_reader, sock_writer = await self._connect_with_timeout()
        except Exception as exc:
            reason = str(exc)
            logger.error("Broker unavailable: %s", reason)
            await self._send_broker_error(reason)
            return

        # Warn if --web-ui was requested but the running broker has no web UI.
        # Skip the probe when we just spawned a fresh daemon (it may not have
        # its HTTP server ready yet and the user's intent is already encoded in
        # the spawn_args passed to the new daemon).
        if self._web_ui_port is not None and not self._new_broker_spawned:
            await asyncio.to_thread(self._warn_web_ui_mismatch)

        # Set up asyncio stdin/stdout if not injected
        stdin_reader = self._stdin
        if stdin_reader is None:
            stdin_reader = await self._make_stdin_reader()

        stdout_writer = self._stdout
        if stdout_writer is None:
            stdout_writer = await self._make_stdout_writer()

        try:
            await self._run_bridge(stdin_reader, stdout_writer, sock_reader, sock_writer)
        finally:
            # Close socket — broker is not signalled
            try:
                sock_writer.close()
                await sock_writer.wait_closed()
            except Exception:
                pass
            logger.debug("BrokerProxy disconnected from %s", self._config.socket_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _send_broker_error(self, reason: str) -> None:
        """Write a JSON-RPC -32001 error response to stdout and flush.

        Called when the broker is unavailable (connection timeout, spawn
        failure, refused).  Uses ``id: null`` because the incoming request
        id cannot be reliably read during the error path.
        """
        payload = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32001,
                        "message": f"Broker unavailable: {reason}",
                    },
                }
            )
            + "\n"
        )
        writer = self._stdout
        if writer is None:
            try:
                writer = await self._make_stdout_writer()
            except Exception as exc:
                logger.error("Could not open stdout writer for error response: %s", exc)
                return
        writer.write(payload.encode())
        with contextlib.suppress(Exception):
            await writer.drain()

    def _warn_web_ui_mismatch(self) -> None:
        """Warn to stderr if the running broker does not expose the web UI port.

        Attempts a TCP connection to ``127.0.0.1:{web_ui_port}`` with a 0.5 s
        timeout.  If the port is not accepting connections the running broker
        was started without ``--web-ui``; an actionable warning is printed so
        the user knows how to fix it.  The MCP session continues regardless.

        Safe to call from a thread (via ``asyncio.to_thread``) so the event
        loop is not blocked during the probe.
        """
        port = self._web_ui_port
        if port is None:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
            # Port is accepting connections — web UI is present; nothing to warn.
            logger.debug("Web UI probe succeeded on port %d.", port)
        except OSError:
            print(
                f"Warning: broker is running without --web-ui on port {port}. "
                "Restart the broker to enable the dashboard.\n"
                "  Hint: stop the running broker "
                "(rm ~/.mcpbridge_wrapper/broker.sock ~/.mcpbridge_wrapper/broker.pid) "
                "then reconnect with --broker --web-ui.",
                file=sys.stderr,
            )

    def _check_version_mismatch(self) -> bool:
        """Return True if the running daemon's version differs from this proxy's.

        Returns False (no mismatch) when the version file does not exist — this
        handles the backwards-compatible case where an older daemon did not
        write a version file.
        """
        version_file = self._config.version_file
        if not version_file.exists():
            return False
        try:
            daemon_version = version_file.read_text().strip()
        except OSError:
            return False
        if daemon_version == __version__:
            return False
        logger.warning(
            "Broker version mismatch: daemon=%s, proxy=%s",
            daemon_version,
            __version__,
        )
        return True

    def _pid_belongs_to_broker(self, pid: int) -> bool:
        """Return True when PID command line matches broker daemon shape."""
        try:
            cmdline = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "command="],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return False
        return "mcpbridge_wrapper" in cmdline and "--broker-daemon" in cmdline

    def _stop_stale_daemon(self) -> None:
        """Stop a running broker daemon via SIGTERM + wait + file cleanup."""
        pid_file = self._config.pid_file
        if not pid_file.exists():
            return
        try:
            pid = int(pid_file.read_text().strip())
        except (ValueError, OSError):
            return

        if not self._pid_belongs_to_broker(pid):
            logger.warning(
                "PID %d from %s is not a broker daemon; cleaning stale files without SIGTERM.",
                pid,
                pid_file,
            )
            self._cleanup_broker_files()
            return

        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            # Already dead or not ours — just clean up files.
            self._cleanup_broker_files()
            return

        # Wait up to 3 seconds for the process to exit.
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)

        self._cleanup_broker_files()

    def _cleanup_broker_files(self) -> None:
        """Remove broker PID, socket, and version files."""
        for path in (
            self._config.pid_file,
            self._config.socket_path,
            self._config.version_file,
        ):
            path.unlink(missing_ok=True)

    async def _spawn_broker_if_needed(self) -> None:
        """Spawn the broker daemon if not already running.

        Uses a filesystem exclusive lock (``fcntl.flock``) to prevent two
        proxy processes from spawning competing daemons simultaneously (the
        double-spawn race condition that occurs when an MCP client toggles
        rapidly).  The second proxy waiter acquires the lock only after the
        first has finished spawning, then re-checks liveness and short-circuits
        to the connect path if the broker appeared while it was waiting.

        The lock is held for the entire spawn + socket-poll window so that
        concurrent processes queue rather than race.  It is released
        automatically when the file descriptor is closed — including on process
        crash — so no stale-lock cleanup is required.
        """
        pid_file = self._config.pid_file
        socket_path = self._config.socket_path
        lock_file = pid_file.with_suffix(".lock")

        # Ensure the config directory exists before opening the lock file.
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        loop = asyncio.get_running_loop()

        with open(lock_file, "w") as lock_fd:
            # Acquire exclusive lock in a thread so the event loop stays free.
            await loop.run_in_executor(None, fcntl.flock, lock_fd.fileno(), fcntl.LOCK_EX)

            # --- critical section: re-check liveness under lock ---
            # A concurrent proxy may have spawned the daemon while we waited.

            # Check if broker is already running via PID file.
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    os.kill(pid, 0)
                    if not self._pid_belongs_to_broker(pid):
                        logger.warning(
                            "Live PID %d from %s is not a broker daemon; cleaning stale files.",
                            pid,
                            pid_file,
                        )
                        self._cleanup_broker_files()
                    else:
                        # Daemon is alive — check for version mismatch.
                        if self._check_version_mismatch():
                            logger.info("Stopping stale broker (version mismatch)…")
                            await loop.run_in_executor(None, self._stop_stale_daemon)
                            # Fall through to spawn a new daemon.
                        else:
                            logger.debug("Broker already running (PID %d); skipping spawn.", pid)
                            return
                except (ValueError, ProcessLookupError, PermissionError):
                    logger.debug("Stale PID file; will spawn broker.")

            # Check if socket already exists and is actually alive.
            # A stale socket file left after a crash passes exists() but refuses connections.
            if socket_path.exists():
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(1.0)
                        s.connect(str(socket_path))
                    # Connection succeeded — broker is alive.
                    logger.debug("Broker socket present and accepting connections; skipping spawn.")
                    return
                except OSError:
                    logger.warning(
                        "Stale socket found (broker not accepting connections);"
                        " removing stale files."
                    )
                    socket_path.unlink(missing_ok=True)
                    pid_file.unlink(missing_ok=True)
                    self._config.version_file.unlink(missing_ok=True)
                    # Fall through to spawn.

            logger.info("Spawning broker daemon…")
            import subprocess

            spawn_args = list(self._spawn_args)
            if "--broker-daemon" not in spawn_args:
                spawn_args.insert(0, "--broker-daemon")

            self._new_broker_spawned = True
            subprocess.Popen(
                [sys.executable, "-m", "mcpbridge_wrapper", *spawn_args],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Poll for socket appearance while holding the lock so concurrent
            # proxies wait and then find the broker alive on their re-check.
            deadline = loop.time() + self._connect_timeout
            while loop.time() < deadline:
                if socket_path.exists():
                    logger.debug("Broker socket appeared.")
                    return
                await asyncio.sleep(0.2)

            raise TimeoutError(
                f"Broker socket did not appear within {self._connect_timeout}s at {socket_path}"
            )

    async def _connect_with_timeout(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to the broker Unix socket, retrying until timeout."""
        socket_path = str(self._config.socket_path)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._connect_timeout
        last_exc: Exception = FileNotFoundError(f"Socket not found: {socket_path}")

        while loop.time() < deadline:
            try:
                reader, writer = await asyncio.open_unix_connection(socket_path)
                logger.debug("Connected to broker at %s", socket_path)
                return reader, writer
            except (FileNotFoundError, ConnectionRefusedError) as exc:
                last_exc = exc
                await asyncio.sleep(0.2)

        raise TimeoutError(
            f"Could not connect to broker socket {socket_path} within {self._connect_timeout}s"
        ) from last_exc

    async def _run_bridge(
        self,
        stdin_reader: asyncio.StreamReader,
        stdout_writer: asyncio.StreamWriter,
        sock_reader: asyncio.StreamReader,
        sock_writer: asyncio.StreamWriter,
    ) -> None:
        """Run bidirectional forward until one side reaches EOF."""
        stdin_to_sock = asyncio.ensure_future(
            self._forward_stream(stdin_reader, sock_writer, "stdin→socket")
        )
        sock_to_stdout = asyncio.ensure_future(
            self._forward_stream(sock_reader, stdout_writer, "socket→stdout")
        )

        done, pending = await asyncio.wait(
            [stdin_to_sock, sock_to_stdout],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel the remaining task
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

        # Re-raise any exception from completed tasks (except EOF which is normal)
        for task in done:
            exc = task.exception()
            if exc is not None and not isinstance(exc, (EOFError, ConnectionResetError)):
                logger.debug("Bridge task ended with: %s", exc)

    async def _forward_stream(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        label: str,
    ) -> None:
        """Read lines from ``reader`` and write them to ``writer``."""
        while True:
            try:
                line = await reader.readline()
            except (asyncio.CancelledError, GeneratorExit):
                return
            except Exception as exc:
                logger.debug("%s: read error: %s", label, exc)
                return

            if not line:
                # EOF
                logger.debug("%s: EOF", label)
                return

            try:
                writer.write(line)
                await writer.drain()
            except Exception as exc:
                logger.debug("%s: write error: %s", label, exc)
                return

    @staticmethod
    async def _make_stdin_reader() -> asyncio.StreamReader:
        """Wrap sys.stdin.buffer as an asyncio StreamReader."""
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)
        return reader

    @staticmethod
    async def _make_stdout_writer() -> asyncio.StreamWriter:
        """Wrap sys.stdout.buffer as an asyncio StreamWriter.

        Uses StreamReaderProtocol (which inherits FlowControlMixin) so that
        StreamWriter.drain() can call protocol._drain_helper() without raising
        AttributeError.  BaseProtocol does not implement _drain_helper, which
        would cause the bridge to silently exit after the first flushed write.
        """
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        transport, _ = await loop.connect_write_pipe(lambda: protocol, sys.stdout.buffer)
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        return writer
