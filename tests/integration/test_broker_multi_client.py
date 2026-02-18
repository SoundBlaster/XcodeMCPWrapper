"""Integration tests for broker multi-client stability (P13-T5)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

import pytest
import pytest_asyncio

from mcpbridge_wrapper.broker.daemon import BrokerDaemon
from mcpbridge_wrapper.broker.transport import UnixSocketServer
from mcpbridge_wrapper.broker.types import BrokerConfig, BrokerState


@pytest.fixture
def upstream_echo_script(tmp_path: Path) -> Path:
    """Create a lightweight upstream process that echoes JSON-RPC requests."""
    script = tmp_path / "upstream_echo.py"
    script.write_text(
        "import json\n"
        "import sys\n"
        "for raw in sys.stdin:\n"
        "    line = raw.strip()\n"
        "    if not line:\n"
        "        continue\n"
        "    msg = json.loads(line)\n"
        "    request_id = msg.get('id')\n"
        "    if request_id is None:\n"
        "        continue\n"
        "    response = {\n"
        "        'jsonrpc': '2.0',\n"
        "        'id': request_id,\n"
        "        'result': {\n"
        "            'method': msg.get('method'),\n"
        "            'params': msg.get('params', {}),\n"
        "        },\n"
        "    }\n"
        "    print(json.dumps(response, separators=(',', ':')), flush=True)\n"
    )
    return script


@pytest.fixture
def broker_config(upstream_echo_script: Path) -> Iterator[BrokerConfig]:
    """Create a short Unix-socket path config suitable for macOS limits."""
    short_dir = Path(tempfile.mkdtemp(dir="/tmp", prefix="mcpb"))
    try:
        yield BrokerConfig(
            socket_path=short_dir / "b.sock",
            pid_file=short_dir / "b.pid",
            upstream_cmd=[sys.executable, "-u", str(upstream_echo_script)],
            reconnect_backoff_cap=1,
            queue_ttl=2,
            graceful_shutdown_timeout=1,
        )
    finally:
        shutil.rmtree(short_dir, ignore_errors=True)


async def _start_broker(config: BrokerConfig) -> BrokerDaemon:
    daemon = BrokerDaemon(config)
    transport = UnixSocketServer(config, daemon)
    daemon._transport = transport  # noqa: SLF001
    await daemon.start()
    return daemon


@pytest_asyncio.fixture
async def running_broker(broker_config: BrokerConfig) -> AsyncIterator[BrokerDaemon]:
    daemon = await _start_broker(broker_config)
    try:
        yield daemon
    finally:
        await daemon.stop()


async def _wait_for_sessions_to_close(daemon: BrokerDaemon, timeout: float = 2.0) -> None:
    transport = daemon._transport  # noqa: SLF001
    assert transport is not None

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if not transport.sessions:
            return
        await asyncio.sleep(0.02)

    raise AssertionError("Expected all client sessions to be closed")


async def _send_request(
    config: BrokerConfig,
    request_id: int | str,
    seq: int,
    method: str = "tools/call",
) -> dict[str, Any]:
    reader, writer = await asyncio.open_unix_connection(str(config.socket_path))

    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {"seq": seq},
    }
    writer.write((json.dumps(request, separators=(",", ":")) + "\n").encode())
    await writer.drain()

    raw = await asyncio.wait_for(reader.readline(), timeout=2.0)
    writer.close()
    with contextlib.suppress(Exception):
        await writer.wait_closed()

    assert raw, "Expected a response line from broker"
    return json.loads(raw.decode())


@pytest.mark.asyncio
async def test_sequential_short_lived_clients_reuse_single_upstream_bridge(
    broker_config: BrokerConfig,
    running_broker: BrokerDaemon,
) -> None:
    initial_upstream_pid = running_broker.status()["upstream_pid"]
    assert initial_upstream_pid is not None

    observed_upstream_pids = set()

    for seq in range(1, 11):
        response = await _send_request(broker_config, request_id=seq, seq=seq)
        assert response["id"] == seq
        assert response["result"]["params"]["seq"] == seq
        observed_upstream_pids.add(running_broker.status()["upstream_pid"])
        await _wait_for_sessions_to_close(running_broker)

    assert observed_upstream_pids == {initial_upstream_pid}
    assert running_broker.state == BrokerState.READY


@pytest.mark.asyncio
async def test_concurrent_clients_remain_stable_under_load(
    broker_config: BrokerConfig,
    running_broker: BrokerDaemon,
) -> None:
    initial_upstream_pid = running_broker.status()["upstream_pid"]
    assert initial_upstream_pid is not None

    async def _client(seq: int) -> dict[str, Any]:
        request_id = f"req-{seq}"
        return await _send_request(
            broker_config,
            request_id=request_id,
            seq=seq,
            method="tools/list",
        )

    client_count = 24
    responses = await asyncio.gather(*(_client(seq) for seq in range(client_count)))

    by_id = {response["id"]: response for response in responses}
    assert len(by_id) == client_count

    for seq in range(client_count):
        request_id = f"req-{seq}"
        assert request_id in by_id
        assert by_id[request_id]["result"]["method"] == "tools/list"
        assert by_id[request_id]["result"]["params"]["seq"] == seq

    await _wait_for_sessions_to_close(running_broker)
    assert running_broker.status()["upstream_pid"] == initial_upstream_pid
    assert running_broker.state == BrokerState.READY


@pytest.mark.asyncio
async def test_broker_mode_launches_upstream_once_for_many_short_lived_clients(
    broker_config: BrokerConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launch_count = 0
    create_subprocess_exec = asyncio.create_subprocess_exec

    async def _counted_create_subprocess(*args: Any, **kwargs: Any) -> asyncio.subprocess.Process:
        nonlocal launch_count
        launch_count += 1
        return await create_subprocess_exec(*args, **kwargs)

    monkeypatch.setattr(
        "mcpbridge_wrapper.broker.daemon.asyncio.create_subprocess_exec",
        _counted_create_subprocess,
    )

    daemon = await _start_broker(broker_config)
    try:
        for seq in range(1, 13):
            response = await _send_request(broker_config, request_id=seq, seq=seq)
            assert response["id"] == seq

        assert launch_count == 1
    finally:
        await daemon.stop()
