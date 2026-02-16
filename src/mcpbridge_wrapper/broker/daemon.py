"""Persistent broker daemon for mcpbridge-wrapper.

This module is a stub. Full implementation is delivered in P13-T2.

The BrokerDaemon owns a single ``xcrun mcpbridge`` upstream subprocess and
exposes a Unix domain socket for local MCP client proxies to connect to.
It multiplexes JSON-RPC traffic between N clients and one upstream bridge.

Lifecycle states
----------------
INIT → READY ↔ RECONNECTING → STOPPING → STOPPED

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md for the full
state-machine diagram and sequence diagrams.
"""

from __future__ import annotations

from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState


class BrokerDaemon:
    """Long-lived process that owns one upstream xcrun mcpbridge subprocess.

    This is a stub class. All methods raise NotImplementedError until P13-T2
    provides the full implementation.
    """

    def __init__(self, config: BrokerConfig) -> None:
        """Initialise daemon with the given configuration."""
        self._config = config
        self._state = BrokerState.INIT

    @property
    def state(self) -> BrokerState:
        """Current lifecycle state."""
        return self._state

    async def start(self) -> None:
        """Start the broker: create socket, write PID file, launch upstream.

        Raises:
            RuntimeError: If another broker instance is already running.
        """
        raise NotImplementedError("BrokerDaemon.start() is implemented in P13-T2")

    async def stop(self) -> None:
        """Gracefully shut down the broker.

        Drains in-flight requests up to ``config.graceful_shutdown_timeout``
        seconds, then terminates the upstream subprocess and removes socket/PID.
        """
        raise NotImplementedError("BrokerDaemon.stop() is implemented in P13-T2")

    async def run_forever(self) -> None:
        """Start and block until a shutdown signal is received."""
        raise NotImplementedError("BrokerDaemon.run_forever() is implemented in P13-T2")
