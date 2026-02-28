"""Client proxy mode for the persistent broker.

The BrokerProxy is the short-lived per-MCP-client process.  It connects to
the broker's Unix domain socket and bridges the MCP client's stdio transport
to the broker, forwarding JSON-RPC messages in both directions.

This allows existing MCP clients configured for stdio to transparently
use the persistent broker without any client-side changes beyond their
command configuration (adding ``--broker-connect`` flag).

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md §3.7 for the
sequence diagram of the proxy connect/disconnect lifecycle.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys

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
        absent before connecting.  Corresponds to the ``--broker-spawn`` CLI
        flag.
    connect_timeout:
        Maximum seconds to wait for the broker socket to become available.
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
        """
        if self._auto_spawn:
            await self._spawn_broker_if_needed()

        sock_reader, sock_writer = await self._connect_with_timeout()

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

    async def _spawn_broker_if_needed(self) -> None:
        """Spawn the broker daemon if not already running.

        Checks the PID file for a live process.  If absent or stale, launches
        the broker daemon in a detached subprocess and polls the socket path
        until it appears (up to ``connect_timeout`` seconds).
        """
        pid_file = self._config.pid_file
        socket_path = self._config.socket_path

        # Check if broker is already running
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)
                logger.debug("Broker already running (PID %d)", pid)
                return
            except (ValueError, ProcessLookupError, PermissionError):
                logger.debug("Stale PID file; will spawn broker.")

        # Check if socket already exists (race condition: broker started without PID file yet)
        if socket_path.exists():
            logger.debug("Broker socket already present; skipping spawn.")
            return

        logger.info("Spawning broker daemon…")
        import subprocess

        spawn_args = list(self._spawn_args)
        if "--broker-daemon" not in spawn_args:
            spawn_args.insert(0, "--broker-daemon")

        subprocess.Popen(
            [sys.executable, "-m", "mcpbridge_wrapper", *spawn_args],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Poll for socket appearance
        loop = asyncio.get_running_loop()
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
        """Wrap sys.stdout.buffer as an asyncio StreamWriter."""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.connect_write_pipe(asyncio.BaseProtocol, sys.stdout.buffer)
        writer = asyncio.StreamWriter(transport, protocol, None, loop)
        return writer
