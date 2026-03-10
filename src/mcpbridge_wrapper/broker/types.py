"""Shared types for the persistent broker subsystem.

This module defines the data structures used across broker components.
All types are stubs pending full implementation in P13-T2 and P13-T3.
"""

from __future__ import annotations

import asyncio
import enum
from dataclasses import dataclass, field
from pathlib import Path


class BrokerState(enum.Enum):
    """Lifecycle states for the broker daemon."""

    INIT = "init"
    READY = "ready"
    RECONNECTING = "reconnecting"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class BrokerConfig:
    """Configuration for a broker daemon instance.

    Attributes:
        socket_path: Path to the Unix domain socket file.
        pid_file: Path to the PID lock file.
        upstream_cmd: Command to launch the upstream bridge process.
        reconnect_backoff_cap: Maximum seconds to wait between reconnect attempts.
        queue_ttl: Seconds a pending request may wait during reconnection before
            being rejected with JSON-RPC error -32001.
        graceful_shutdown_timeout: Seconds to wait for in-flight requests to
            complete before forceful shutdown.
    """

    socket_path: Path
    pid_file: Path
    upstream_cmd: list[str]
    reconnect_backoff_cap: int = 30
    queue_ttl: int = 60
    graceful_shutdown_timeout: int = 5

    @property
    def version_file(self) -> Path:
        """Path to the version stamp file, derived from pid_file's directory."""
        return self.pid_file.parent / "broker.version"

    @classmethod
    def default(cls) -> BrokerConfig:
        """Return config with default paths under ~/.mcpbridge_wrapper/."""
        base = Path.home() / ".mcpbridge_wrapper"
        return cls(
            socket_path=base / "broker.sock",
            pid_file=base / "broker.pid",
            upstream_cmd=["xcrun", "mcpbridge"],
        )


@dataclass
class ClientSession:
    """Represents one connected MCP client.

    Attributes:
        session_id: Monotonic counter assigned on connect; used for ID remapping.
        peer_uid: OS-level UID of the connecting process (verified via getpeereid).
        connected_at: Unix timestamp of connection establishment.
        writer: asyncio StreamWriter for sending responses back to the client.
        pending: Map from broker-remapped request ID to the asyncio Future that
            will be resolved when the upstream response arrives.
    """

    session_id: int
    peer_uid: int
    connected_at: float
    writer: asyncio.StreamWriter
    pending: dict[int, asyncio.Future] = field(default_factory=dict)
    # Maps string original IDs to their local integer alias (for string-ID support)
    string_id_map: dict[str, int] = field(default_factory=dict)
    # Maps integer original IDs to their local integer alias (reversible; FU-P13-T11)
    int_id_map: dict[int, int] = field(default_factory=dict)
    # Reverse map: local_seq → original_id (int or str) for O(1) restoration
    id_restore: dict[int, int | str] = field(default_factory=dict)
    # Set once the client finishes the MCP initialize -> initialized lifecycle.
    initialized: bool = False
    # Synthetic tools/list_changed notification to flush after client initialization.
    pending_tools_list_changed: bool = False
    # Shared monotonic counter for allocating local alias IDs within this session
    _next_local_id: int = field(default=0, repr=False)


@dataclass
class PendingRequest:
    """Tracks a single in-flight JSON-RPC request.

    Attributes:
        client_id: session_id of the originating client.
        original_id: The request ID as sent by the client (int or str).
        broker_id: The remapped ID forwarded to the upstream bridge.
        queued_at: Unix timestamp for TTL enforcement during reconnection.
    """

    client_id: int
    original_id: int | str
    broker_id: int
    queued_at: float
