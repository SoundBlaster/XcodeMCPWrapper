"""Unix domain socket transport for the persistent broker.

The UnixSocketServer accepts incoming client connections on the broker socket
and hands each connection to a per-client handler that multiplexes JSON-RPC
traffic to/from the upstream bridge managed by BrokerDaemon.

Request ID remapping
--------------------
Outgoing request IDs are namespaced to prevent collisions across clients.
Each session maintains a monotonic counter (``ClientSession._next_local_id``)
and two forward maps (``string_id_map``, ``int_id_map``) plus a unified
reverse map (``id_restore``) so every original ID round-trips exactly:

    local_seq  = _alloc_local_id(session)          # 1 … 2^20-1
    broker_id  = (session_id << 20) | local_seq

Responses from upstream carry broker_id; the server extracts
``client_id = broker_id >> 20``, restores ``original_id`` via
``session.id_restore[local_seq]`` in O(1), routes the response back
to the correct ClientSession, and releases alias bookkeeping once complete.

This design preserves large (> 20-bit), negative, and concurrent integer IDs
without truncation or aliasing.  (Replaces the lossy ``original_id & 0xFFFFF``
mask from P13-T3; see FU-P13-T11.)

JSON-RPC notifications (``id == null``) are broadcast to all active clients.

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md for sequence diagrams.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import socket
import struct
import time
from typing import TYPE_CHECKING, Any

from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState, ClientSession

if TYPE_CHECKING:
    from mcpbridge_wrapper.broker.daemon import BrokerDaemon

logger = logging.getLogger(__name__)

# Bit-shift for ID namespacing: session_id occupies the upper bits.
_SESSION_SHIFT = 20
_ID_MASK = (1 << _SESSION_SHIFT) - 1  # 0xFFFFF


def _alloc_local_id(session: ClientSession) -> int:  # noqa: F821
    """Allocate the next local sequence ID within *session*'s 20-bit namespace.

    The counter is shared across string and integer ID allocations so that no
    two original IDs of any type can receive the same local alias within a
    single session.  The counter wraps at ``2^_SESSION_SHIFT - 1`` (skipping
    0) rather than at ``2^_SESSION_SHIFT`` so that 0 is reserved for
    notifications/null IDs. Active aliases already present in ``id_restore``
    are skipped so wrapped allocations never collide with in-flight requests.
    """
    max_aliases = _ID_MASK
    for _ in range(max_aliases):
        session._next_local_id += 1
        if session._next_local_id >= (1 << _SESSION_SHIFT):
            session._next_local_id = 1  # wrap, skipping 0
        if session._next_local_id not in session.id_restore:
            return session._next_local_id

    raise RuntimeError("No free local request IDs available in this session")


def _release_local_alias(session: ClientSession, local_alias: int) -> int | str | None:
    """Release alias bookkeeping for ``local_alias`` and return original ID.

    The returned original ID is used to restore response IDs.  Forward maps are
    pruned only when they still point to the released alias so newer requests
    with the same original ID are preserved.
    """
    original_id = session.id_restore.pop(local_alias, None)
    if isinstance(original_id, str):
        if session.string_id_map.get(original_id) == local_alias:
            session.string_id_map.pop(original_id, None)
    elif isinstance(original_id, int) and session.int_id_map.get(original_id) == local_alias:
        session.int_id_map.pop(original_id, None)
    return original_id


def _get_peer_uid(writer: asyncio.StreamWriter) -> int:
    """Return the effective UID of the process connected on *writer*.

    Tries peer-credential mechanisms in this order:
    1. macOS/BSD ``getpeereid()``
    2. BSD/macOS ``LOCAL_PEERCRED`` via ``getsockopt``
    3. Linux ``SO_PEERCRED`` via ``getsockopt``

    Raises:
        OSError: If the underlying socket is unavailable or neither platform
        API is supported — callers must treat this as a security failure
        and reject the connection (fail-closed).
    """
    raw_sock: Any = writer.get_extra_info("socket")
    if raw_sock is None:
        raise OSError("No underlying socket available via get_extra_info('socket')")

    errors: list[str] = []

    # macOS / BSD: socket has a getpeereid() method
    if hasattr(raw_sock, "getpeereid"):
        try:
            uid, _gid = raw_sock.getpeereid()
            return int(uid)
        except OSError as exc:
            errors.append(f"getpeereid failed: {exc}")

    # BSD/macOS LOCAL_PEERCRED returns credential bytes containing UID.
    local_peercred = getattr(socket, "LOCAL_PEERCRED", None)
    if local_peercred is not None:
        sol_local = getattr(socket, "SOL_LOCAL", 0)
        try:
            creds = raw_sock.getsockopt(sol_local, local_peercred, struct.calcsize("3i"))
            if len(creds) < struct.calcsize("2i"):
                raise OSError(f"LOCAL_PEERCRED payload too short: got {len(creds)} bytes")
            _version, uid = struct.unpack_from("2i", creds)
            return int(uid)
        except OSError as exc:
            errors.append(f"LOCAL_PEERCRED failed: {exc}")

    # Linux: SO_PEERCRED returns a packed (pid, uid, gid) struct of 3 C ints.
    so_peercred = getattr(socket, "SO_PEERCRED", None)
    if so_peercred is not None:
        try:
            creds = raw_sock.getsockopt(
                socket.SOL_SOCKET,
                so_peercred,
                struct.calcsize("3i"),
            )
            _pid, uid, _gid = struct.unpack("3i", creds)
            return int(uid)
        except OSError as exc:
            errors.append(f"SO_PEERCRED failed: {exc}")

    if errors:
        raise OSError("Could not determine peer UID: " + "; ".join(errors))

    raise OSError("No supported peer credential API available")


class UnixSocketServer:
    """Accepts and manages local client connections over a Unix domain socket.

    The server is tightly coupled to a :class:`BrokerDaemon` instance which
    owns the upstream subprocess.  Call :meth:`start` once the daemon is READY,
    and :meth:`stop` before the daemon shuts down.

    Parameters
    ----------
    config:
        Shared broker configuration (socket path, TTL settings, etc.).
    daemon:
        The owning :class:`BrokerDaemon` instance. Used to write requests to
        the upstream subprocess stdin and to read the daemon state.
    """

    def __init__(
        self,
        config: BrokerConfig,
        daemon: BrokerDaemon,
        *,
        metrics: Any | None = None,
        audit: Any | None = None,
    ) -> None:
        """Initialise the server with the given broker configuration."""
        self._config = config
        self._daemon = daemon
        self._metrics = metrics
        self._audit = audit
        self._server: asyncio.AbstractServer | None = None
        self._sessions: dict[int, ClientSession] = {}
        self._next_session_id: int = 1
        self._stop_event: asyncio.Event = asyncio.Event()
        # broker_id -> (tool_name, start_time)
        self._pending_tool_requests: dict[int, tuple[str, float]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def sessions(self) -> dict[int, ClientSession]:
        """Currently connected client sessions (read-only view)."""
        return self._sessions

    async def start(self) -> None:
        """Bind to the Unix socket and begin accepting connections.

        The socket file is created with owner-only permissions (``0600``) so
        that only the same OS user can attempt a connection.  Every accepted
        connection is additionally peer-credential-verified inside
        :meth:`_handle_client`.
        """
        socket_path = str(self._config.socket_path)
        self._stop_event.clear()
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=socket_path,
        )
        # Restrict socket access to the owning user only.
        # The socket file is created by start_unix_server above; we tighten
        # permissions immediately so the window of wider access is minimal.
        if self._config.socket_path.is_socket():
            self._config.socket_path.chmod(0o600)
            logger.debug("Socket permissions set to 0600: %s", socket_path)
        logger.info("UnixSocketServer listening on %s", socket_path)

    async def stop(self) -> None:
        """Stop accepting connections and drain in-flight requests.

        Sends JSON-RPC error ``-32001`` to each client that has outstanding
        pending requests, then closes all writer streams.  Waits up to
        ``config.graceful_shutdown_timeout`` seconds for clean completion.
        """
        self._stop_event.set()

        if self._server is not None:
            self._server.close()
            with contextlib.suppress(Exception):
                await asyncio.wait_for(
                    self._server.wait_closed(),
                    timeout=self._config.graceful_shutdown_timeout,
                )

        # Notify all connected clients of pending request failures
        for session in list(self._sessions.values()):
            await self._drain_session(session)

        logger.info("UnixSocketServer stopped")

    async def route_upstream_response(self, line: str) -> None:
        """Route a single JSON-RPC line received from upstream.

        Called by :class:`BrokerDaemon` each time a complete line arrives from
        the upstream subprocess stdout.

        - If the message has a valid broker ``id``, it is routed to the
          originating :class:`ClientSession` and the original ``id`` is restored.
        - If the message has ``id == null`` or no ``id`` field, it is broadcast
          to all connected clients.
        - Malformed lines are logged and silently dropped.
        """
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.debug("Malformed upstream line (%s): %r", exc, line)
            return

        if not isinstance(msg, dict):
            logger.debug("Upstream sent non-object JSON: %r", msg)
            return

        raw_id = msg.get("id")

        if raw_id is None:
            # Notification → broadcast
            await self._broadcast(line)
            return

        if not isinstance(raw_id, int):
            logger.debug("Unexpected non-integer broker_id from upstream: %r", raw_id)
            return

        broker_id: int = raw_id
        self._record_tool_response_metrics(broker_id, msg)
        client_id = broker_id >> _SESSION_SHIFT
        int_local_id = broker_id & _ID_MASK

        session = self._sessions.get(client_id)
        if session is None:
            logger.debug(
                "No session for client_id=%d (broker_id=%d); dropping response.",
                client_id,
                broker_id,
            )
            return

        # Restore original request ID via O(1) reverse map and release alias.
        # Fall back to int_local_id for sessions that pre-populated pending
        # without going through _process_client_line (e.g. legacy test fixtures).
        released_original_id = _release_local_alias(session, int_local_id)
        original_id: int | str | None = (
            released_original_id if released_original_id is not None else int_local_id
        )

        # Rebuild the message with the original ID
        msg["id"] = original_id
        restored_line = json.dumps(msg, separators=(",", ":"))

        # Fulfil the pending future (if any) and write to the client
        fut = session.pending.pop(broker_id, None)
        if fut is not None and not fut.done():
            fut.set_result(restored_line)

        await self._write_to_session(session, restored_line)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle the lifecycle of a single connected client.

        Connections are rejected immediately with a JSON-RPC ``-32003`` error if:

        - The peer UID cannot be determined (fail-closed).
        - The peer UID differs from the broker's own UID.
        """
        session_id = self._next_session_id
        self._next_session_id += 1

        # Verify peer credentials before registering the session.
        try:
            peer_uid = _get_peer_uid(writer)
        except Exception as exc:
            logger.warning(
                "Cannot verify peer UID for session %d: %s — rejecting connection.",
                session_id,
                exc,
            )
            await self._send_uid_error_and_close(writer)
            return

        own_uid = os.getuid()
        if peer_uid != own_uid:
            logger.warning(
                "Rejected connection from UID %d (own UID %d) on session %d.",
                peer_uid,
                own_uid,
                session_id,
            )
            await self._send_uid_error_and_close(writer)
            return

        session = ClientSession(
            session_id=session_id,
            peer_uid=peer_uid,
            connected_at=time.time(),
            writer=writer,
        )
        self._sessions[session_id] = session
        logger.debug("Client connected: session_id=%d uid=%d", session_id, peer_uid)

        try:
            await self._read_client_loop(session, reader)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("Client session %d error: %s", session_id, exc)
        finally:
            self._sessions.pop(session_id, None)
            with contextlib.suppress(Exception):
                writer.close()
                await writer.wait_closed()
            logger.debug("Client disconnected: session_id=%d", session_id)

    async def _send_uid_error_and_close(self, writer: asyncio.StreamWriter) -> None:
        """Send JSON-RPC -32003 (Forbidden) to *writer* and close the connection.

        Used to reject connections that fail peer-UID verification.
        """
        msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32003, "message": "Forbidden: UID mismatch"},
            },
            separators=(",", ":"),
        )
        try:
            writer.write((msg + "\n").encode())
            await writer.drain()
        except Exception:
            pass
        with contextlib.suppress(Exception):
            writer.close()
            await writer.wait_closed()

    async def _read_client_loop(
        self,
        session: ClientSession,
        reader: asyncio.StreamReader,
    ) -> None:
        """Read JSON-RPC requests from a single client and forward to upstream."""
        while not self._stop_event.is_set():
            try:
                raw = await asyncio.wait_for(reader.readline(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception as exc:
                logger.warning("Read error from session %d: %s", session.session_id, exc)
                break

            if not raw:
                # Client disconnected
                break

            line = raw.decode(errors="replace").rstrip("\n")
            if not line:
                continue

            await self._process_client_line(session, line)

    async def _process_client_line(self, session: ClientSession, line: str) -> None:
        """Parse, remap, and forward one JSON-RPC line from a client."""
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.debug(
                "Malformed request from session %d (%s): %r",
                session.session_id,
                exc,
                line,
            )
            await self._send_parse_error(session, None)
            return

        if not isinstance(msg, dict):
            await self._send_parse_error(session, None)
            return

        method_name = msg.get("method") if isinstance(msg.get("method"), str) else None
        if method_name == "initialize" and self._metrics is not None:
            self._record_client_identity(msg)

        raw_id = msg.get("id")
        is_notification = raw_id is None

        broker_id: int | None = None
        local_alias: int | None = None

        if not is_notification:
            if method_name == "tools/list":
                # Strict MCP clients cache the first tools/list result. Hold the
                # request until the broker has its own warm cache populated.
                if not self._daemon.tools_catalog_ready.is_set():
                    try:
                        await asyncio.wait_for(
                            self._daemon.tools_catalog_ready.wait(),
                            timeout=float(self._config.queue_ttl),
                        )
                    except asyncio.TimeoutError:
                        await self._send_error(
                            session,
                            raw_id,
                            -32001,
                            "Broker tools catalog not ready — request TTL exceeded",
                        )
                        return
            else:
                # Gate: wait until the upstream has completed its initialize round-trip.
                # This prevents clients from receiving empty or error responses during the
                # Xcode approval window or other upstream restart scenarios.
                if not self._daemon.upstream_initialized.is_set():
                    try:
                        await asyncio.wait_for(
                            self._daemon.upstream_initialized.wait(),
                            timeout=float(self._config.queue_ttl),
                        )
                    except asyncio.TimeoutError:
                        await self._send_error(
                            session,
                            raw_id,
                            -32001,
                            "Broker upstream not ready — request TTL exceeded",
                        )
                        return

            if self._daemon.state not in (BrokerState.READY, BrokerState.RECONNECTING):
                await self._send_error(
                    session,
                    raw_id,
                    -32001,
                    "Broker unavailable",
                )
                return

            # Cache hit: serve tools/list directly from the broker cache without
            # forwarding to the upstream.  The cached message ID is replaced with
            # the client's original ID before writing.
            if method_name == "tools/list" and self._daemon._tools_list_cache is not None:
                if not isinstance(raw_id, (int, str)):
                    await self._send_parse_error(session, raw_id)
                    return
                cached_msg = json.loads(self._daemon._tools_list_cache)
                cached_msg["id"] = raw_id
                await self._write_to_session(session, json.dumps(cached_msg, separators=(",", ":")))
                return

            # Remap the request ID using a reversible per-session counter so all
            # valid JSON-RPC IDs (large, negative, string) round-trip exactly.
            original_id = raw_id
            try:
                local_alias = _alloc_local_id(session)
            except RuntimeError:
                await self._send_error(
                    session,
                    original_id,
                    -32001,
                    "Broker request ID space exhausted for this session",
                )
                return

            if isinstance(original_id, str):
                session.string_id_map[original_id] = local_alias
            elif isinstance(original_id, int):
                session.int_id_map[original_id] = local_alias
            else:
                await self._send_parse_error(session, original_id)
                return
            session.id_restore[local_alias] = original_id

            broker_id = (session.session_id << _SESSION_SHIFT) | local_alias
            msg["id"] = broker_id

            # Track pending request
            loop = asyncio.get_event_loop()
            fut: asyncio.Future[str] = loop.create_future()
            session.pending[broker_id] = fut

            if method_name == "tools/call" and broker_id is not None and self._metrics is not None:
                tool_name = self._extract_tool_call_name(msg)
                if tool_name:
                    self._metrics.record_request(tool_name, request_id=str(broker_id))
                    self._pending_tool_requests[broker_id] = (tool_name, time.time())

        remapped_line = json.dumps(msg, separators=(",", ":"))

        # Write to upstream
        upstream = self._daemon._upstream  # noqa: SLF001
        if upstream is None or upstream.stdin is None:
            if not is_notification:
                await self._send_error(
                    session,
                    raw_id,
                    -32001,
                    "Upstream bridge not available",
                )
                if broker_id is not None:
                    session.pending.pop(broker_id, None)
                    self._record_broker_tool_failure(
                        broker_id,
                        error_code=-32001,
                        error_message="Upstream bridge not available",
                    )
                if local_alias is not None:
                    _release_local_alias(session, local_alias)
            return

        try:
            upstream.stdin.write((remapped_line + "\n").encode())
            await upstream.stdin.drain()
            logger.debug(
                "client %d → upstream: %s",
                session.session_id,
                remapped_line,
            )
        except Exception as exc:
            logger.warning(
                "Failed to write to upstream from session %d: %s",
                session.session_id,
                exc,
            )
            if not is_notification:
                await self._send_error(session, raw_id, -32001, "Upstream write failed")
                if broker_id is not None:
                    session.pending.pop(broker_id, None)
                    self._record_broker_tool_failure(
                        broker_id,
                        error_code=-32001,
                        error_message="Upstream write failed",
                    )
                if local_alias is not None:
                    _release_local_alias(session, local_alias)

    async def _broadcast(self, line: str) -> None:
        """Write ``line`` to all connected client sessions."""
        for session in list(self._sessions.values()):
            await self._write_to_session(session, line)

    async def _write_to_session(self, session: ClientSession, line: str) -> None:
        """Write a single JSON-RPC line to a client session's writer."""
        try:
            session.writer.write((line + "\n").encode())
            await session.writer.drain()
        except Exception as exc:
            logger.debug("Write error to session %d: %s", session.session_id, exc)

    async def _send_parse_error(
        self,
        session: ClientSession,
        request_id: Any,
    ) -> None:
        """Send a JSON-RPC parse error (-32700) to the client."""
        await self._send_error(session, request_id, -32700, "Parse error")

    async def _send_error(
        self,
        session: ClientSession,
        request_id: Any,
        code: int,
        message: str,
    ) -> None:
        """Send a JSON-RPC error response to the client."""
        error_response = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            },
            separators=(",", ":"),
        )
        await self._write_to_session(session, error_response)

    async def _drain_session(self, session: ClientSession) -> None:
        """Send -32001 error for all pending requests and close the session."""
        for broker_id, fut in list(session.pending.items()):
            if not fut.done():
                fut.cancel()
            self._record_broker_tool_failure(
                broker_id,
                error_code=-32001,
                error_message="Broker shutting down",
            )
            # Restore original_id via O(1) reverse map.
            int_local_id = broker_id & _ID_MASK
            released_original_id = _release_local_alias(session, int_local_id)
            original_id: int | str = (
                released_original_id if released_original_id is not None else int_local_id
            )
            await self._send_error(session, original_id, -32001, "Broker shutting down")
        session.pending.clear()

        with contextlib.suppress(Exception):
            session.writer.close()
            await session.writer.wait_closed()

    def _record_client_identity(self, msg: dict[str, Any]) -> None:
        """Capture client identity from initialize params for shared metrics."""
        if self._metrics is None:
            return

        params = msg.get("params")
        if not isinstance(params, dict):
            self._metrics.set_client_info("unknown", "unknown")
            return

        client_info = params.get("clientInfo")
        if not isinstance(client_info, dict):
            self._metrics.set_client_info("unknown", "unknown")
            return

        name = client_info.get("name")
        version = client_info.get("version")
        if isinstance(name, str) and isinstance(version, str):
            self._metrics.set_client_info(name, version)
        else:
            self._metrics.set_client_info("unknown", "unknown")

    @staticmethod
    def _extract_tool_call_name(msg: dict[str, Any]) -> str | None:
        """Extract MCP tool name from tools/call payload."""
        params = msg.get("params")
        if not isinstance(params, dict):
            return None
        name = params.get("name")
        return name if isinstance(name, str) else None

    @staticmethod
    def _parse_error_details(msg: dict[str, Any]) -> tuple[bool, int | None, str | None]:
        """Parse error status for broker-routed responses."""
        error = msg.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            raw_message = error.get("message")
            parsed_code = code if isinstance(code, int) else None
            parsed_message = raw_message if isinstance(raw_message, str) else None
            return True, parsed_code, parsed_message

        result = msg.get("result")
        if isinstance(result, dict) and result.get("isError") is True:
            parsed_result_message: str | None = None
            content = result.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_value = item.get("text")
                        if isinstance(text_value, str) and text_value.strip():
                            parsed_result_message = text_value
                            break
            return True, None, parsed_result_message

        return False, None, None

    def _record_tool_response_metrics(self, broker_id: int, msg: dict[str, Any]) -> None:
        """Record response latency/error for tracked broker tool requests."""
        pending = self._pending_tool_requests.pop(broker_id, None)
        if pending is None or self._metrics is None:
            return

        tool_name, start_time = pending
        latency_ms = (time.time() - start_time) * 1000.0
        is_error, error_code, error_message = self._parse_error_details(msg)

        self._metrics.record_response(
            tool_name,
            request_id=str(broker_id),
            error=is_error,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
        )

        if self._audit is not None:
            self._audit.log(
                tool_name=tool_name,
                request_id=str(broker_id),
                latency_ms=latency_ms,
                error=error_message if is_error else None,
                error_code=error_code if is_error else None,
                direction="response",
            )

    def _record_broker_tool_failure(
        self,
        broker_id: int,
        *,
        error_code: int,
        error_message: str,
    ) -> None:
        """Record telemetry for broker-generated failures before upstream response exists."""
        pending = self._pending_tool_requests.pop(broker_id, None)
        if pending is None:
            return
        if self._metrics is None:
            return

        tool_name, start_time = pending
        latency_ms = (time.time() - start_time) * 1000.0

        self._metrics.record_response(
            tool_name,
            request_id=str(broker_id),
            error=True,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
        )

        if self._audit is not None:
            self._audit.log(
                tool_name=tool_name,
                request_id=str(broker_id),
                latency_ms=latency_ms,
                error=error_message,
                error_code=error_code,
                direction="response",
            )
