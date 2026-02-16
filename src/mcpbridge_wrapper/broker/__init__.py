"""Persistent broker subsystem for mcpbridge-wrapper.

This package implements the long-lived broker process that owns a single
``xcrun mcpbridge`` upstream connection and multiplexes multiple MCP clients
through it, eliminating repeated Xcode permission prompts and reducing
per-session startup latency.

Architecture overview
---------------------
- ``BrokerDaemon`` — owns the upstream subprocess and lifecycle management
- ``UnixSocketServer`` — accepts and manages local client connections
- ``BrokerProxy`` — per-client stdio proxy that connects to the broker socket
- ``BrokerConfig`` — unified configuration dataclass
- ``BrokerState`` — lifecycle state enum

See ``SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md`` for the full
design specification, sequence diagrams, and ADR.

Implementation status
---------------------
P13-T1 (this task): Types + stubs only.
P13-T2: BrokerDaemon full implementation.
P13-T3: UnixSocketServer + JSON-RPC multiplexing.
P13-T4: BrokerProxy + CLI flags.
"""

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.proxy import BrokerProxy
from mcpbridge_wrapper.broker.transport import UnixSocketServer
from mcpbridge_wrapper.broker.types import (
    BrokerConfig,
    BrokerState,
    ClientSession,
    PendingRequest,
)

__all__ = [
    "BrokerConfig",
    "BrokerDaemon",
    "BrokerProxy",
    "BrokerState",
    "ClientSession",
    "PendingRequest",
    "UnixSocketServer",
]
