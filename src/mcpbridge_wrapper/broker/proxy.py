"""Client proxy mode for the persistent broker.

This module is a stub. Full implementation is delivered in P13-T4.

The BrokerProxy is the short-lived per-MCP-client process. It connects to
the broker's Unix domain socket and bridges the MCP client's stdio transport
to the broker, forwarding JSON-RPC messages in both directions.

This allows existing MCP clients configured for stdio to transparently
use the persistent broker without any client-side changes beyond their
command configuration (adding ``--broker-connect`` flag).

See SPECS/ARCHIVE/P13-T1_*/broker_architecture_spec.md §3.7 for the
sequence diagram of the proxy connect/disconnect lifecycle.
"""

from __future__ import annotations

from mcpbridge_wrapper.broker.types import BrokerConfig


class BrokerProxy:
    """Forwards stdio ↔ Unix socket for a single MCP client.

    This is a stub class. All methods raise NotImplementedError until P13-T4
    provides the full implementation.
    """

    def __init__(self, config: BrokerConfig) -> None:
        """Initialise the proxy with the given broker configuration."""
        self._config = config

    async def run(self) -> None:
        """Connect to broker and forward stdio until client disconnects."""
        raise NotImplementedError("BrokerProxy.run() is implemented in P13-T4")
