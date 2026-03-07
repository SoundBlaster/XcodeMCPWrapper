"""Tests for broker doctor diagnostics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from mcpbridge_wrapper.doctor import (
    DashboardDiagnostics,
    DoctorReport,
    LocalBrokerDiagnostics,
    _find_listener_pids_for_port,
    _pid_exists,
    _read_local_pid,
    _read_local_version,
    _read_process_command,
    classify_doctor_report,
    collect_dashboard_diagnostics,
    collect_doctor_report,
    collect_local_broker_diagnostics,
    render_doctor_report,
    run_doctor,
)
from mcpbridge_wrapper.tui import TUIRuntimeConfig


def _runtime(base_url: str = "http://127.0.0.1:8080") -> TUIRuntimeConfig:
    return TUIRuntimeConfig(
        base_url=base_url,
        auth_header=None,
        log_path=Path("/tmp/broker.log"),
        pid_file=Path("/tmp/broker.pid"),
        socket_path=Path("/tmp/broker.sock"),
        version_file=Path("/tmp/broker.version"),
    )


def _local(
    *,
    pid_file_present: bool = True,
    pid: int | None = 100,
    pid_running: bool = True,
    socket_present: bool = True,
    version_file_present: bool = True,
    version: str | None = "0.4.1",
    version_mismatch: bool = False,
) -> LocalBrokerDiagnostics:
    return LocalBrokerDiagnostics(
        pid_file="/tmp/broker.pid",
        pid_file_present=pid_file_present,
        pid=pid,
        pid_running=pid_running,
        socket_path="/tmp/broker.sock",
        socket_present=socket_present,
        version_file="/tmp/broker.version",
        version_file_present=version_file_present,
        version=version,
        version_mismatch=version_mismatch,
    )


def _dashboard(
    *,
    health_ok: bool = False,
    health_error: str | None = "Cannot reach http://127.0.0.1:8080: [Errno 61] Connection refused",
    listener_pids: list[int] | None = None,
    listener_commands: dict[int, str] | None = None,
    control: dict | None = None,
    broker_status: dict | None = None,
    backend_error: str | None = "GET /api/control failed: Not Found",
) -> DashboardDiagnostics:
    return DashboardDiagnostics(
        base_url="http://127.0.0.1:8080",
        port=8080,
        listener_pids=list(listener_pids or []),
        listener_commands=dict(listener_commands or {}),
        health_ok=health_ok,
        health_error=health_error,
        control=control,
        broker_status=broker_status,
        backend_error=backend_error,
    )


class TestDoctorHelpers:
    """Tests for low-level doctor helpers and data accessors."""

    def test_dashboard_properties_surface_service_and_broker_payload(self) -> None:
        dashboard = DashboardDiagnostics(
            base_url="http://127.0.0.1:8080",
            port=8080,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": True,
                "service_name": "broker-daemon",
                "broker": {"state": "ready"},
            },
        )

        assert dashboard.service_name == "broker-daemon"
        assert dashboard.broker_available is True
        assert dashboard.broker_payload == {"state": "ready"}

    def test_pid_exists_handles_lookup_and_permission_errors(self) -> None:
        with patch("mcpbridge_wrapper.doctor.os.kill", return_value=None):
            assert _pid_exists(123) is True

        with patch("mcpbridge_wrapper.doctor.os.kill", side_effect=ProcessLookupError):
            assert _pid_exists(123) is False

        with patch("mcpbridge_wrapper.doctor.os.kill", side_effect=PermissionError):
            assert _pid_exists(123) is True

    def test_read_local_pid_handles_missing_invalid_and_running_pid(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.pid"
        assert _read_local_pid(str(missing)) == (None, False)

        invalid = tmp_path / "invalid.pid"
        invalid.write_text("not-a-pid")
        assert _read_local_pid(str(invalid)) == (None, False)

        valid = tmp_path / "broker.pid"
        valid.write_text("321")
        with patch("mcpbridge_wrapper.doctor._pid_exists", return_value=True):
            assert _read_local_pid(str(valid)) == (321, True)

    def test_read_local_version_handles_missing_error_and_empty(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.version"
        assert _read_local_version(str(missing)) is None

        empty = tmp_path / "empty.version"
        empty.write_text("")
        assert _read_local_version(str(empty)) is None

        broken = tmp_path / "broken.version"
        broken.write_text("0.4.1")
        with patch("builtins.open", side_effect=OSError("denied")):
            assert _read_local_version(str(broken)) is None

    def test_find_listener_pids_for_port_handles_none_duplicates_and_oserror(self) -> None:
        assert _find_listener_pids_for_port(None) == []

        completed = type("Completed", (), {"stdout": "123\n456\n123\njunk\n"})()
        with patch("mcpbridge_wrapper.doctor.subprocess.run", return_value=completed):
            assert _find_listener_pids_for_port(8080) == [123, 456]

        with patch("mcpbridge_wrapper.doctor.subprocess.run", side_effect=OSError):
            assert _find_listener_pids_for_port(8080) == []

    def test_read_process_command_handles_success_and_failure(self) -> None:
        with patch(
            "mcpbridge_wrapper.doctor.subprocess.check_output",
            return_value="python -m mcpbridge_wrapper --broker-daemon\n",
        ):
            assert _read_process_command(777) == "python -m mcpbridge_wrapper --broker-daemon"

        with patch(
            "mcpbridge_wrapper.doctor.subprocess.check_output",
            side_effect=OSError("ps failed"),
        ):
            assert _read_process_command(777) is None

    def test_collect_local_broker_diagnostics_reads_runtime_files(self, tmp_path: Path) -> None:
        pid_file = tmp_path / "broker.pid"
        pid_file.write_text("654")
        socket_path = tmp_path / "broker.sock"
        socket_path.write_text("sock")
        version_file = tmp_path / "broker.version"
        version_file.write_text("0.4.1")
        runtime = TUIRuntimeConfig(
            base_url="http://127.0.0.1:8080",
            auth_header=None,
            log_path=tmp_path / "broker.log",
            pid_file=pid_file,
            socket_path=socket_path,
            version_file=version_file,
        )

        with patch("mcpbridge_wrapper.doctor._pid_exists", return_value=True):
            diagnostics = collect_local_broker_diagnostics(runtime)

        assert diagnostics.pid == 654
        assert diagnostics.pid_running is True
        assert diagnostics.socket_present is True
        assert diagnostics.version == "0.4.1"

    def test_collect_dashboard_diagnostics_collects_successful_probes(self) -> None:
        runtime = _runtime()

        with patch(
            "mcpbridge_wrapper.doctor._find_listener_pids_for_port",
            return_value=[111],
        ), patch(
            "mcpbridge_wrapper.doctor._read_process_command",
            return_value="python -m mcpbridge_wrapper --broker-daemon",
        ), patch(
            "mcpbridge_wrapper.tui.BrokerTUIClient._request_json",
            return_value={"status": "ok"},
        ), patch(
            "mcpbridge_wrapper.tui.BrokerTUIClient.probe_backend",
            return_value=(
                {"service_name": "broker-daemon", "can_stop": True},
                {"available": True, "service_name": "broker-daemon", "broker": {"state": "ready"}},
            ),
        ):
            diagnostics = collect_dashboard_diagnostics(runtime)

        assert diagnostics.listener_pids == [111]
        assert diagnostics.listener_commands[111] == "python -m mcpbridge_wrapper --broker-daemon"
        assert diagnostics.health_ok is True
        assert diagnostics.backend_error is None
        assert diagnostics.service_name == "broker-daemon"

    def test_collect_dashboard_diagnostics_handles_failed_probes(self) -> None:
        runtime = _runtime()

        with patch(
            "mcpbridge_wrapper.doctor._find_listener_pids_for_port",
            return_value=[],
        ), patch(
            "mcpbridge_wrapper.tui.BrokerTUIClient._request_json",
            side_effect=RuntimeError("health down"),
        ), patch(
            "mcpbridge_wrapper.tui.BrokerTUIClient.probe_backend",
            side_effect=RuntimeError("backend down"),
        ):
            diagnostics = collect_dashboard_diagnostics(runtime)

        assert diagnostics.health_ok is False
        assert diagnostics.health_error == "health down"
        assert diagnostics.backend_error == "backend down"


class TestClassifyDoctorReport:
    """Tests for doctor diagnosis classification."""

    def test_classify_version_mismatch(self) -> None:
        report = classify_doctor_report(
            _runtime(),
            _local(version="0.0.1-old", version_mismatch=True),
            _dashboard(listener_pids=[], backend_error=None),
        )

        assert report.ok is False
        assert report.code == "version-mismatch"
        assert "does not match" in report.summary.lower()

    def test_classify_healthy_broker_backed_runtime(self) -> None:
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            backend_error=None,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": True,
                "service_name": "broker-daemon",
                "broker": {
                    "state": "ready",
                    "pid": 100,
                    "upstream_pid": 101,
                    "upstream_alive": True,
                    "upstream_initialized": True,
                    "connected_clients": 2,
                    "reconnect_attempt": 0,
                },
            },
        )

        report = classify_doctor_report(_runtime(), _local(), dashboard)

        assert report.ok is True
        assert report.code == "healthy"
        assert "healthy" in report.summary.lower()
        assert "--broker" in report.next_action

    def test_classify_broker_backed_runtime_not_ready(self) -> None:
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            backend_error=None,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": True,
                "service_name": "broker-daemon",
                "broker": {
                    "state": "reconnecting",
                    "pid": 100,
                    "upstream_pid": 101,
                    "upstream_alive": False,
                    "upstream_initialized": False,
                    "connected_clients": 0,
                    "reconnect_attempt": 2,
                },
            },
        )

        report = classify_doctor_report(_runtime(), _local(), dashboard)

        assert report.ok is False
        assert report.code == "broker-degraded"
        assert any("not alive" in line for line in report.evidence_lines)
        assert any("reconnecting" in line for line in report.evidence_lines)

    def test_classify_broker_running_without_dashboard(self) -> None:
        report = classify_doctor_report(_runtime(), _local(), _dashboard(listener_pids=[]))

        assert report.ok is False
        assert report.code == "broker-without-dashboard"
        assert "no broker-backed dashboard" in report.summary.lower()
        assert (
            report.next_action
            == "Restart the dedicated host with `mcpbridge-wrapper --broker-stop && "
            "mcpbridge-wrapper --broker-console`."
        )

    def test_classify_wrong_service_on_dashboard_port(self) -> None:
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            listener_pids=[501],
            listener_commands={501: "python -m http.server 8080"},
            control={"service_name": "mcpbridge-wrapper", "can_stop": False},
            broker_status={"available": False, "service_name": "mcpbridge-wrapper", "broker": None},
            backend_error=None,
        )

        report = classify_doctor_report(
            _runtime(),
            _local(
                pid_file_present=False,
                pid=None,
                pid_running=False,
                socket_present=False,
                version_file_present=False,
                version=None,
            ),
            dashboard,
        )

        assert report.ok is False
        assert report.code == "wrong-service"
        assert "not the dedicated broker host" in report.summary.lower()
        assert (
            report.next_action == "Stop the existing listener or retry startup with "
            "`mcpbridge-wrapper --broker-console --web-ui-restart`."
        )

    def test_classify_broker_daemon_with_unavailable_runtime_status(self) -> None:
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": False,
                "service_name": "broker-daemon",
                "broker": None,
                "error": "upstream reconnecting",
            },
            backend_error=None,
        )

        report = classify_doctor_report(_runtime(), _local(), dashboard)

        assert report.ok is False
        assert report.code == "broker-degraded"
        assert "runtime status is unavailable" in report.summary.lower()
        assert any("upstream reconnecting" in line for line in report.evidence_lines)

    def test_classify_stale_runtime_files(self) -> None:
        report = classify_doctor_report(
            _runtime(),
            _local(pid_running=False, socket_present=True, version_file_present=True),
            _dashboard(listener_pids=[], backend_error=None),
        )

        assert report.ok is False
        assert report.code == "stale-runtime"
        assert "stale" in report.summary.lower()
        assert "--broker-stop" in report.next_action

    def test_classify_port_occupied_before_broker_startup(self) -> None:
        dashboard = _dashboard(
            health_ok=False,
            listener_pids=[777],
            listener_commands={777: "node /tmp/other-service.js"},
            control=None,
            broker_status=None,
            backend_error="GET /api/control failed: Not Found",
        )

        report = classify_doctor_report(
            _runtime(),
            _local(pid_file_present=False, pid=None, pid_running=False, socket_present=False),
            dashboard,
        )

        assert report.ok is False
        assert report.code == "port-occupied"
        assert "occupied" in report.summary.lower()
        assert (
            report.next_action == "Free the port or retry startup with "
            "`mcpbridge-wrapper --broker-console --web-ui-restart`."
        )

    def test_classify_broker_not_running_without_any_endpoint(self) -> None:
        report = classify_doctor_report(
            _runtime(),
            _local(
                pid_file_present=False,
                pid=None,
                pid_running=False,
                socket_present=False,
                version_file_present=False,
                version=None,
            ),
            _dashboard(
                listener_pids=[],
                health_error=None,
                backend_error=None,
            ),
        )

        assert report.ok is False
        assert report.code == "broker-not-running"
        assert "no running broker daemon" in report.summary.lower()


class TestRenderDoctorReport:
    """Tests for doctor output rendering."""

    def test_render_report_includes_summary_sections(self) -> None:
        report = DoctorReport(
            code="broker-not-running",
            ok=False,
            summary="No running broker daemon was detected.",
            next_action="Start with `mcpbridge-wrapper --broker-console`.",
            exit_code=1,
            python_runtime_lines=["Package Version: 0.4.1"],
            local_state_lines=["PID File: /tmp/broker.pid (missing)"],
            dashboard_lines=["Endpoint: http://127.0.0.1:8080"],
            broker_runtime_lines=[],
            evidence_lines=["No live broker PID or broker-backed dashboard was found."],
        )

        rendered = render_doctor_report(report)

        assert "mcpbridge-wrapper doctor" in rendered
        assert "Status: ISSUE" in rendered
        assert "Next Action:" in rendered
        assert "Python Runtime" in rendered
        assert "Evidence" in rendered

    def test_render_report_marks_healthy_status(self) -> None:
        report = DoctorReport(
            code="healthy",
            ok=True,
            summary="Broker daemon and broker-backed dashboard are healthy.",
            next_action="Connect with `--broker`.",
            exit_code=0,
            python_runtime_lines=["Package Version: 0.4.1"],
            local_state_lines=["Daemon PID: 100 (running)"],
            dashboard_lines=["Endpoint: http://127.0.0.1:8080"],
            broker_runtime_lines=["State: ready"],
            evidence_lines=["Dashboard is reachable and reports service `broker-daemon`."],
        )

        rendered = render_doctor_report(report)

        assert "Status: OK" in rendered
        assert "Broker Runtime" in rendered
        assert "State: ready" in rendered


class TestCollectDoctorReport:
    """Light integration tests for doctor collection helpers."""

    def test_collect_dashboard_runtime_report_uses_live_version(self) -> None:
        runtime = _runtime()
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            backend_error=None,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": True,
                "service_name": "broker-daemon",
                "broker": {
                    "state": "ready",
                    "pid": 100,
                    "upstream_pid": 101,
                    "upstream_alive": True,
                    "upstream_initialized": True,
                    "connected_clients": 0,
                    "reconnect_attempt": 0,
                },
            },
        )

        with patch("mcpbridge_wrapper.doctor.__version__", "9.9.9"):
            report = classify_doctor_report(
                runtime,
                _local(version="9.9.9", version_mismatch=False),
                dashboard,
            )

        assert report.ok is True
        assert any("Package Version: 9.9.9" in line for line in report.python_runtime_lines)

    def test_collect_doctor_report_uses_runtime_and_collectors(self) -> None:
        runtime = _runtime(base_url="http://127.0.0.1:9191")
        local = _local()
        dashboard = _dashboard(
            health_ok=True,
            health_error=None,
            backend_error=None,
            control={"service_name": "broker-daemon", "can_stop": True},
            broker_status={
                "available": True,
                "service_name": "broker-daemon",
                "broker": {
                    "state": "ready",
                    "pid": 100,
                    "upstream_pid": 101,
                    "upstream_alive": True,
                    "upstream_initialized": True,
                    "connected_clients": 0,
                    "reconnect_attempt": 0,
                },
            },
        )

        with patch("mcpbridge_wrapper.doctor.build_tui_runtime", return_value=runtime), patch(
            "mcpbridge_wrapper.doctor.collect_local_broker_diagnostics",
            return_value=local,
        ) as collect_local, patch(
            "mcpbridge_wrapper.doctor.collect_dashboard_diagnostics",
            return_value=dashboard,
        ) as collect_dashboard:
            report = collect_doctor_report(web_ui_port=9191, web_ui_config=None)

        assert report.ok is True
        collect_local.assert_called_once_with(runtime)
        collect_dashboard.assert_called_once_with(runtime)

    def test_run_doctor_prints_rendered_report_and_returns_exit_code(self) -> None:
        report = DoctorReport(
            code="broker-not-running",
            ok=False,
            summary="No running broker daemon was detected.",
            next_action="Start with `mcpbridge-wrapper --broker-console`.",
            exit_code=1,
            python_runtime_lines=["Package Version: 0.4.1"],
            local_state_lines=["PID File: /tmp/broker.pid (missing)"],
            dashboard_lines=["Endpoint: http://127.0.0.1:8080"],
            broker_runtime_lines=[],
            evidence_lines=["No live broker PID or broker-backed dashboard was found."],
        )

        with patch("mcpbridge_wrapper.doctor.collect_doctor_report", return_value=report), patch(
            "builtins.print"
        ) as print_mock:
            exit_code = run_doctor(web_ui_port=None, web_ui_config=None)

        assert exit_code == 1
        print_mock.assert_called_once()
        rendered = print_mock.call_args.args[0]
        assert "mcpbridge-wrapper doctor" in rendered
