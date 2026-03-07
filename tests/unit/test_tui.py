"""Tests for the broker terminal frontend."""

import base64
import io
import json
import sys
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from mcpbridge_wrapper.tui import (
    BrokerTUI,
    BrokerTUIClient,
    BrokerTUISnapshot,
    TUIRuntimeConfig,
    _extract_http_error,
    _read_local_pid,
    _read_local_version,
    build_tui_runtime,
    render_screen,
    run_tui,
    tail_log_lines,
)


class _FakeHTTPResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self._payload


class _FakeWindow:
    def __init__(self, keys: list[int]) -> None:
        self._keys = list(keys)
        self.lines: list[tuple[int, int, str, int]] = []
        self.timeout_value = None
        self.nodelay_value = None
        self.refreshed = False

    def nodelay(self, value: bool) -> None:
        self.nodelay_value = value

    def timeout(self, value: int) -> None:
        self.timeout_value = value

    def getmaxyx(self) -> tuple[int, int]:
        return (20, 80)

    def getch(self) -> int:
        if not self._keys:
            return -1
        return self._keys.pop(0)

    def erase(self) -> None:
        return None

    def addnstr(self, row: int, col: int, text: str, width: int) -> None:
        self.lines.append((row, col, text, width))

    def refresh(self) -> None:
        self.refreshed = True


def _runtime(
    *,
    auth_header: str | None = None,
    timeout_seconds: float = 1.5,
    base_url: str = "http://127.0.0.1:8080",
) -> TUIRuntimeConfig:
    return TUIRuntimeConfig(
        base_url=base_url,
        auth_header=auth_header,
        log_path=Path("/tmp/broker.log"),
        pid_file=Path("/tmp/broker.pid"),
        socket_path=Path("/tmp/broker.sock"),
        version_file=Path("/tmp/broker.version"),
        timeout_seconds=timeout_seconds,
    )


def _snapshot() -> BrokerTUISnapshot:
    return BrokerTUISnapshot(
        base_url="http://127.0.0.1:8080",
        service_name="broker-daemon",
        can_stop=True,
        available=True,
        broker={"state": "ready", "pid": 1, "socket_path": "/tmp/broker.sock"},
        recent_events=["ready"],
        local_pid=1,
        local_daemon_running=True,
        local_socket_present=True,
        local_daemon_version="0.4.1",
        local_pid_file="/tmp/broker.pid",
        local_socket_path="/tmp/broker.sock",
        local_version_file="/tmp/broker.version",
    )


class TestBuildTUIRuntime:
    """Tests for runtime resolution helpers."""

    def test_build_runtime_uses_config_and_auth(self, tmp_path: Path) -> None:
        config_path = tmp_path / "webui.json"
        config_path.write_text(
            json.dumps(
                {
                    "host": "127.0.0.1",
                    "port": 9090,
                    "auth": {
                        "enabled": True,
                        "username": "alice",
                        "password": "secret",
                    },
                }
            )
        )

        runtime = build_tui_runtime(web_ui_port=None, web_ui_config=str(config_path))

        assert runtime.base_url == "http://127.0.0.1:9090"
        expected = "Basic " + base64.b64encode(b"alice:secret").decode("ascii")
        assert runtime.auth_header == expected
        assert runtime.log_path.name == "broker.log"
        assert runtime.pid_file.name == "broker.pid"
        assert runtime.socket_path.name == "broker.sock"
        assert runtime.version_file.name == "broker.version"

    def test_build_runtime_port_override_wins(self, tmp_path: Path) -> None:
        config_path = tmp_path / "webui.json"
        config_path.write_text(json.dumps({"port": 8080}))

        runtime = build_tui_runtime(web_ui_port=9191, web_ui_config=str(config_path))

        assert runtime.base_url == "http://127.0.0.1:9191"


class TestTailLogLines:
    """Tests for broker log tailing."""

    def test_tail_log_lines_reads_recent_entries(self, tmp_path: Path) -> None:
        log_path = tmp_path / "broker.log"
        log_path.write_text("line-1\nline-2\nline-3\n")

        assert tail_log_lines(log_path, max_lines=2) == ["line-2", "line-3"]

    def test_tail_log_lines_reports_missing_log(self, tmp_path: Path) -> None:
        lines = tail_log_lines(tmp_path / "missing.log", max_lines=3)

        assert len(lines) == 1
        assert "no broker log" in lines[0]

    def test_tail_log_lines_handles_zero_limit(self, tmp_path: Path) -> None:
        assert tail_log_lines(tmp_path / "broker.log", max_lines=0) == []

    def test_tail_log_lines_reports_empty_log(self, tmp_path: Path) -> None:
        log_path = tmp_path / "broker.log"
        log_path.write_text("")

        assert tail_log_lines(log_path, max_lines=3) == ["(broker log is empty)"]


class TestBrokerTUIClient:
    """Tests for HTTP aggregation and control helpers."""

    def test_fetch_snapshot_combines_control_status_and_log_tail(self) -> None:
        runtime = _runtime()
        client = BrokerTUIClient(runtime)

        with patch.object(
            client,
            "_request_json",
            side_effect=[
                {"service_name": "broker-daemon", "can_stop": True},
                {
                    "available": True,
                    "service_name": "broker-daemon",
                    "broker": {
                        "state": "ready",
                        "pid": 101,
                        "upstream_pid": 202,
                        "connected_clients": 3,
                    },
                },
            ],
        ) as request_json, patch(
            "mcpbridge_wrapper.tui.tail_log_lines", return_value=["ready"]
        ) as tail_lines:
            snapshot = client.fetch_snapshot("Refreshed.")

        assert snapshot.service_name == "broker-daemon"
        assert snapshot.can_stop is True
        assert snapshot.available is True
        assert snapshot.broker is not None
        assert snapshot.broker["connected_clients"] == 3
        assert snapshot.recent_events == ["ready"]
        assert snapshot.status_message == "Refreshed."
        assert snapshot.local_pid is None
        assert snapshot.local_daemon_running is False
        assert request_json.call_args_list == [call("/api/control"), call("/api/broker/status")]
        tail_lines.assert_called_once_with(runtime.log_path, max_lines=runtime.recent_log_lines)

    def test_fetch_snapshot_surfaces_runtime_errors(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch.object(
            client, "_request_json", side_effect=RuntimeError("boom")
        ), patch("mcpbridge_wrapper.tui.tail_log_lines", return_value=["event"]):
            snapshot = client.fetch_snapshot()

        assert snapshot.available is False
        assert snapshot.error_message == "boom"
        assert snapshot.recent_events == ["event"]

    def test_request_stop_returns_backend_message(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch.object(
            client,
            "_request_json",
            return_value={"status": "accepted", "message": "Shutdown requested for broker-daemon."},
        ):
            ok, message = client.request_stop()

        assert ok is True
        assert message == "Shutdown requested for broker-daemon."

    def test_request_stop_returns_default_message_when_backend_omits_one(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch.object(client, "_request_json", return_value={"status": "accepted"}):
            ok, message = client.request_stop()

        assert ok is True
        assert message == "Shutdown requested."

    def test_request_stop_surfaces_runtime_error(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch.object(client, "_request_json", side_effect=RuntimeError("stop unavailable")):
            ok, message = client.request_stop()

        assert ok is False
        assert message == "stop unavailable"

    def test_request_json_success_includes_auth_header(self) -> None:
        client = BrokerTUIClient(_runtime(auth_header="Basic token", timeout_seconds=2.0))
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout):
            headers = dict(request.header_items())
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["auth"] = headers.get("Authorization")
            return _FakeHTTPResponse('{"status": "ok"}')

        with patch("mcpbridge_wrapper.tui.urllib.request.urlopen", side_effect=fake_urlopen):
            payload = client._request_json("/api/control")

        assert payload == {"status": "ok"}
        assert captured == {
            "url": "http://127.0.0.1:8080/api/control",
            "timeout": 2.0,
            "auth": "Basic token",
        }

    def test_request_json_http_error_uses_detail_message(self) -> None:
        client = BrokerTUIClient(_runtime())
        error = urllib.error.HTTPError(
            url="http://127.0.0.1:8080/api/control/stop",
            code=409,
            msg="Conflict",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"Stop control is not available."}'),
        )

        with patch(
            "mcpbridge_wrapper.tui.urllib.request.urlopen", side_effect=error
        ), pytest.raises(RuntimeError, match="Stop control is not available"):
            client._request_json("/api/control/stop", method="POST")

    def test_request_json_url_error_is_actionable(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch(
            "mcpbridge_wrapper.tui.urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ), pytest.raises(RuntimeError, match="Cannot reach http://127.0.0.1:8080: refused"):
            client._request_json("/api/control")

    def test_request_json_rejects_invalid_json(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch(
            "mcpbridge_wrapper.tui.urllib.request.urlopen",
            return_value=_FakeHTTPResponse("not json"),
        ), pytest.raises(RuntimeError, match="returned invalid JSON"):
            client._request_json("/api/control")

    def test_request_json_rejects_non_mapping_payload(self) -> None:
        client = BrokerTUIClient(_runtime())

        with patch(
            "mcpbridge_wrapper.tui.urllib.request.urlopen",
            return_value=_FakeHTTPResponse('["bad"]'),
        ), pytest.raises(RuntimeError, match="unexpected payload"):
            client._request_json("/api/control")


class TestRenderScreen:
    """Tests for pure screen rendering helpers."""

    def test_render_screen_includes_runtime_fields(self) -> None:
        snapshot = BrokerTUISnapshot(
            base_url="http://127.0.0.1:8080",
            service_name="broker-daemon",
            can_stop=True,
            available=True,
            broker={
                "state": "ready",
                "pid": 111,
                "upstream_pid": 222,
                "connected_clients": 2,
                "upstream_alive": True,
                "upstream_initialized": True,
                "tools_list_cached": True,
                "reconnect_attempt": 0,
                "shutdown_requested": False,
                "socket_path": "/tmp/broker.sock",
            },
            recent_events=["ready", "tools/list cached"],
            local_pid=111,
            local_daemon_running=True,
            local_socket_present=True,
            local_daemon_version="0.4.1",
            local_pid_file="/tmp/broker.pid",
            local_socket_path="/tmp/broker.sock",
            local_version_file="/tmp/broker.version",
            status_message="Watching broker.",
        )

        output = "\n".join(render_screen(snapshot, width=80))

        assert "Local Broker Files" in output
        assert "Local Version: 0.4.1" in output
        assert "State: ready" in output
        assert "Connected Clients: 2" in output
        assert "Recent Broker Events" in output
        assert "Watching broker." in output

    def test_render_screen_handles_unavailable_backend(self) -> None:
        snapshot = BrokerTUISnapshot(
            base_url="http://127.0.0.1:8080",
            service_name="unavailable",
            can_stop=False,
            available=False,
            broker=None,
            recent_events=["(no broker log)"],
            local_pid=None,
            local_daemon_running=False,
            local_socket_present=False,
            local_daemon_version=None,
            local_pid_file="/tmp/broker.pid",
            local_socket_path="/tmp/broker.sock",
            local_version_file="/tmp/broker.version",
            error_message="Cannot reach http://127.0.0.1:8080: refused",
        )

        output = "\n".join(render_screen(snapshot, width=80))

        assert "Broker runtime is unavailable." in output
        assert "Cannot reach http://127.0.0.1:8080: refused" in output
        assert "Local Socket Present: no" in output

    def test_render_screen_shows_runtime_warning_when_broker_is_available(self) -> None:
        snapshot = BrokerTUISnapshot(
            base_url="http://127.0.0.1:8080",
            service_name="broker-daemon",
            can_stop=True,
            available=True,
            broker={"state": "reconnecting", "pid": None, "socket_path": ""},
            recent_events=[],
            local_pid=None,
            local_daemon_running=False,
            local_socket_present=False,
            local_daemon_version=None,
            local_pid_file="/tmp/broker.pid",
            local_socket_path="/tmp/broker.sock",
            local_version_file="/tmp/broker.version",
            error_message="degraded runtime",
        )

        output = "\n".join(render_screen(snapshot, width=60))

        assert "Warning: degraded runtime" in output
        assert "(no broker events found)" in output


class TestBrokerTUI:
    """Tests for the thin curses shell."""

    def test_run_loop_renders_and_exits_on_q(self) -> None:
        snapshot = _snapshot()

        class _Client:
            def fetch_snapshot(self, status_message):
                del status_message
                return snapshot

        window = _FakeWindow([ord("q")])
        fake_curses = SimpleNamespace(curs_set=lambda *_args, **_kwargs: None)
        ui = BrokerTUI(_Client())

        with patch.dict(sys.modules, {"curses": fake_curses}):
            result = ui._run_loop(window)

        assert result == 0
        assert window.timeout_value == 100
        assert window.nodelay_value is True
        assert window.refreshed is True
        assert any("Broker Runtime" in line[2] for line in window.lines)

    def test_run_loop_handles_refresh_and_stop_keys(self) -> None:
        snapshot = _snapshot()

        class _Client:
            def __init__(self) -> None:
                self.fetch_calls: list[str | None] = []
                self.request_stop_calls = 0

            def fetch_snapshot(self, status_message):
                self.fetch_calls.append(status_message)
                return snapshot

            def request_stop(self):
                self.request_stop_calls += 1
                return True, "stop requested"

        client = _Client()
        window = _FakeWindow([ord("r"), ord("s"), ord("q")])
        fake_curses = SimpleNamespace(curs_set=lambda *_args, **_kwargs: None)
        ui = BrokerTUI(client)

        with patch.dict(sys.modules, {"curses": fake_curses}):
            result = ui._run_loop(window)

        assert result == 0
        assert client.fetch_calls == [None, None, "stop requested"]
        assert client.request_stop_calls == 1

    def test_run_loop_refreshes_on_timer(self) -> None:
        snapshot = _snapshot()

        class _Client:
            def __init__(self) -> None:
                self.fetch_calls: list[str | None] = []

            def fetch_snapshot(self, status_message):
                self.fetch_calls.append(status_message)
                return snapshot

            def request_stop(self):
                return True, "unused"

        client = _Client()
        window = _FakeWindow([-1, ord("q")])
        fake_curses = SimpleNamespace(curs_set=lambda *_args, **_kwargs: None)
        ui = BrokerTUI(client, refresh_interval_seconds=1.0)

        with patch(
            "mcpbridge_wrapper.tui.time.monotonic", side_effect=[0.0, 2.0, 2.0]
        ), patch.dict(sys.modules, {"curses": fake_curses}):
            result = ui._run_loop(window)

        assert result == 0
        assert client.fetch_calls == [None, None]

    def test_run_uses_curses_wrapper(self) -> None:
        fake_curses = SimpleNamespace(
            wrapper=lambda func: 7,
            curs_set=lambda *_args, **_kwargs: None,
        )
        ui = BrokerTUI(SimpleNamespace())

        with patch.dict(sys.modules, {"curses": fake_curses}):
            assert ui.run() == 7

    def test_run_tui_builds_ui_and_runs_it(self) -> None:
        with patch("mcpbridge_wrapper.tui.BrokerTUI.run", return_value=5) as run_method:
            assert run_tui(_runtime()) == 5

        run_method.assert_called_once()


class TestHelpers:
    """Tests for small formatting and local-state helpers."""

    def test_extract_http_error_prefers_known_fields(self) -> None:
        assert _extract_http_error('{"detail":"fine"}') == "fine"
        assert _extract_http_error('{"message":"hello"}') == "hello"
        assert _extract_http_error('{"error":"boom"}') == "boom"
        assert _extract_http_error("plain text") == "plain text"

    def test_read_local_pid_and_version_helpers(self, tmp_path: Path) -> None:
        pid_file = tmp_path / "broker.pid"
        version_file = tmp_path / "broker.version"
        pid_file.write_text("1234")
        version_file.write_text("0.4.1")

        with patch("mcpbridge_wrapper.tui.os.kill") as os_kill:
            assert _read_local_pid(pid_file) == (1234, True)
            os_kill.assert_called_once_with(1234, 0)

        assert _read_local_version(version_file) == "0.4.1"

    def test_read_local_pid_handles_missing_stale_and_permission(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.pid"
        assert _read_local_pid(missing) == (None, False)

        stale = tmp_path / "stale.pid"
        stale.write_text("9876")
        with patch("mcpbridge_wrapper.tui.os.kill", side_effect=ProcessLookupError):
            assert _read_local_pid(stale) == (9876, False)

        protected = tmp_path / "protected.pid"
        protected.write_text("4321")
        with patch("mcpbridge_wrapper.tui.os.kill", side_effect=PermissionError):
            assert _read_local_pid(protected) == (4321, True)

    def test_read_local_version_handles_missing_and_read_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.version"
        assert _read_local_version(missing) is None

        broken = tmp_path / "broken.version"
        broken.write_text("0.4.1")
        with patch.object(Path, "read_text", side_effect=OSError):
            assert _read_local_version(broken) is None
