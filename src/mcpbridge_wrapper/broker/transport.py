"""Unix domain socket transport for the persistent broker.

This module is a stub. Full implementation is delivered in P13-T3.

The UnixSocketServer accepts incoming client connections on the broker
socket, authenticates them via peer credential verification (getpeereid),
and hands each connection to a ClientSession that multiplexes JSON-RPC
traffic to/from the upstream bridge managed by BrokerDaemon.

Request ID remapping
--------------------
Outgoing request IDs are namespaced:
    broker_id = (client_session_id << 20) | original_id_int

Responses from upstream carry broker_id; the server extracts
``client_id = broker_id >> 20``, restores ``original_id``, and routes
the response back to the correct ClientSession.

JSON-RPC notifications (``id == null``) are broadcast to all active clients.

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md for sequence diagrams.
"""

from __future__ import annotations

from mcpbridge_wrapper.broker.types import BrokerConfig


class UnixSocketServer:
    """Accepts and manages local client connections over a Unix domain socket.

    This is a stub class. All methods raise NotImplementedError until P13-T3
    provides the full implementation.
    """

    def __init__(self, config: BrokerConfig) -> None:
        """Initialise the server with the given broker configuration."""
        self._config = config

    async def start(self) -> None:
        """Bind and begin accepting connections."""
        raise NotImplementedError("UnixSocketServer.start() is implemented in P13-T3")

    async def stop(self) -> None:
        """Close the server socket and disconnect all active sessions."""
        raise NotImplementedError("UnixSocketServer.stop() is implemented in P13-T3")
