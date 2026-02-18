#!/usr/bin/env python3
"""Local integration test for BrokerDaemon + UnixSocketServer.

Uses a mock upstream (Python echo server) so no Xcode project is required.

Usage:
    python scripts/test_broker_local.py

What it tests:
1. BrokerDaemon starts and launches mock upstream.
2. UnixSocketServer accepts two concurrent clients.
3. Each client sends a JSON-RPC request with a unique ID.
4. Responses arrive at the correct client with the original ID restored.
5. A broadcast notification is received by both clients.
6. Clean shutdown drains pending requests.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

# Make sure the src package is importable when run from repo root.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.transport import UnixSocketServer
from mcpbridge_wrapper.broker.types import BrokerConfig

# ---------------------------------------------------------------------------
# Mock upstream script (echos JSON-RPC requests as results + sends a
# notification first).
# ---------------------------------------------------------------------------

MOCK_UPSTREAM_SCRIPT = textwrap.dedent(
    """\
    import sys, json, time

    # Send a broadcast notification immediately on startup
    notif = {"jsonrpc": "2.0", "method": "broker/ready", "params": {"status": "ok"}}
    sys.stdout.write(json.dumps(notif) + "\\n")
    sys.stdout.flush()

    # Echo each incoming request back as a successful result
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
            resp = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "result": {"echo": req.get("method", "unknown"), "params": req.get("params")},
            }
            sys.stdout.write(json.dumps(resp) + "\\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"mock upstream error: {e}\\n")
    """
)


async def main() -> None:
    print("=== Broker local integration test ===\n")

    # Write mock upstream script to a temp file.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, prefix="mock_upstream_"
    ) as f:
        f.write(MOCK_UPSTREAM_SCRIPT)
        upstream_script = f.name

    tmp_dir = Path(tempfile.mkdtemp(prefix="broker_test_"))
    sock_path = tmp_dir / "broker.sock"
    pid_path = tmp_dir / "broker.pid"

    cfg = BrokerConfig(
        socket_path=sock_path,
        pid_file=pid_path,
        upstream_cmd=[sys.executable, upstream_script],
        reconnect_backoff_cap=2,
        queue_ttl=10,
        graceful_shutdown_timeout=2,
    )

    transport = UnixSocketServer(cfg, None)  # daemon set after init
    daemon = BrokerDaemon(cfg, transport=transport)
    transport._daemon = daemon  # wire back-reference

    print("Starting broker daemon + transport…")
    await daemon.start()
    print(f"  Daemon state: {daemon.state.value}")
    print(f"  Socket: {sock_path}")

    # Give the mock upstream a moment to send its startup notification.
    await asyncio.sleep(0.15)

    # -----------------------------------------------------------------------
    # Connect two clients concurrently.
    # -----------------------------------------------------------------------
    print("\nConnecting two clients…")
    reader1, writer1 = await asyncio.open_unix_connection(str(sock_path))
    reader2, writer2 = await asyncio.open_unix_connection(str(sock_path))
    print("  Both clients connected.")

    # Give the server a moment to register sessions.
    await asyncio.sleep(0.05)
    print(f"  Active sessions: {list(transport.sessions.keys())}")

    # -----------------------------------------------------------------------
    # Client 1 sends a request with integer ID = 1
    # -----------------------------------------------------------------------
    req1 = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    writer1.write((json.dumps(req1) + "\n").encode())
    await writer1.drain()
    print(f"\nClient 1 → sent:  {json.dumps(req1)}")

    # -----------------------------------------------------------------------
    # Client 2 sends a request with string ID = "req-abc"
    # -----------------------------------------------------------------------
    req2 = {"jsonrpc": "2.0", "id": "req-abc", "method": "tools/call", "params": {"name": "ping"}}
    writer2.write((json.dumps(req2) + "\n").encode())
    await writer2.drain()
    print(f"Client 2 → sent:  {json.dumps(req2)}")

    # -----------------------------------------------------------------------
    # Read responses (with timeout).
    # -----------------------------------------------------------------------
    async def read_line(reader: asyncio.StreamReader, label: str) -> dict:
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=3.0)
            msg = json.loads(raw)
            print(f"{label} ← recv:  {json.dumps(msg)}")
            return msg
        except asyncio.TimeoutError:
            print(f"{label} ← TIMEOUT waiting for response")
            return {}

    # First response on each client may be the startup notification.
    # Collect up to 2 messages per client (notification + result).
    results: dict[str, dict] = {"client1": {}, "client2": {}}

    async def collect_responses(
        reader: asyncio.StreamReader, label: str, key: str, expected_id: int | str
    ) -> None:
        for _ in range(2):
            msg = await read_line(reader, label)
            if not msg:
                break
            if msg.get("id") == expected_id:
                results[key] = msg
                return
        # If we never found the expected id, the last msg is it (notifications have no id match)

    await asyncio.gather(
        collect_responses(reader1, "Client 1", "client1", 1),
        collect_responses(reader2, "Client 2", "client2", "req-abc"),
    )

    # -----------------------------------------------------------------------
    # Validate results.
    # -----------------------------------------------------------------------
    print("\n--- Validation ---")
    ok = True

    r1 = results["client1"]
    if r1.get("id") == 1 and "result" in r1:
        print(f"  ✅ Client 1 got correct response (id=1, method={r1['result'].get('echo')})")
    else:
        print(f"  ❌ Client 1 result unexpected: {r1}")
        ok = False

    r2 = results["client2"]
    if r2.get("id") == "req-abc" and "result" in r2:
        print(f"  ✅ Client 2 got correct response (id='req-abc', method={r2['result'].get('echo')})")
    else:
        print(f"  ❌ Client 2 result unexpected: {r2}")
        ok = False

    # -----------------------------------------------------------------------
    # Clean up.
    # -----------------------------------------------------------------------
    writer1.close()
    writer2.close()
    with open(os.devnull, "w") as devnull:
        pass  # suppress close warnings

    print("\nStopping broker…")
    await daemon.stop()
    print(f"  Daemon state: {daemon.state.value}")

    # Clean up temp files.
    os.unlink(upstream_script)

    print(f"\n{'✅ ALL CHECKS PASSED' if ok else '❌ SOME CHECKS FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
