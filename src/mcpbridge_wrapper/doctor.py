"""User-facing broker diagnostics for the dedicated-host workflow."""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from mcpbridge_wrapper import __version__
from mcpbridge_wrapper.tui import BrokerTUIClient, TUIRuntimeConfig, build_tui_runtime


@dataclass
class LocalBrokerDiagnostics:
    """Observed local broker state from PID/socket/version files."""

    pid_file: str
    pid_file_present: bool
    pid: int | None
    pid_running: bool
    socket_path: str
    socket_present: bool
    version_file: str
    version_file_present: bool
    version: str | None
    version_mismatch: bool


@dataclass
class DashboardDiagnostics:
    """Observed dashboard endpoint state and ownership details."""

    base_url: str
    port: int | None
    listener_pids: list[int] = field(default_factory=list)
    listener_commands: dict[int, str] = field(default_factory=dict)
    health_ok: bool = False
    health_error: str | None = None
    control: dict[str, Any] | None = None
    broker_status: dict[str, Any] | None = None
    backend_error: str | None = None

    @property
    def service_name(self) -> str | None:
        """Return the reported service name when the endpoint exposes one."""
        for payload in (self.broker_status, self.control):
            if not isinstance(payload, dict):
                continue
            service_name = payload.get("service_name")
            if isinstance(service_name, str) and service_name:
                return service_name
        return None

    @property
    def broker_payload(self) -> dict[str, Any] | None:
        """Return structured broker payload when exposed by the endpoint."""
        if not isinstance(self.broker_status, dict):
            return None
        payload = self.broker_status.get("broker")
        return payload if isinstance(payload, dict) else None

    @property
    def broker_available(self) -> bool:
        """Return whether the endpoint reports broker runtime availability."""
        if not isinstance(self.broker_status, dict):
            return False
        return bool(self.broker_status.get("available"))


@dataclass
class DoctorReport:
    """Rendered doctor result for CLI output and exit-code decisions."""

    code: str
    ok: bool
    summary: str
    next_action: str
    exit_code: int
    python_runtime_lines: list[str]
    local_state_lines: list[str]
    dashboard_lines: list[str]
    broker_runtime_lines: list[str]
    evidence_lines: list[str]


def _pid_exists(pid: int) -> bool:
    """Return True when the process exists and is probeable."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_local_pid(pid_file: str) -> tuple[int | None, bool]:
    """Read a broker PID file and report whether the process is still alive."""
    if not os.path.exists(pid_file):
        return None, False

    try:
        with open(pid_file, encoding="utf-8") as handle:
            pid = int(handle.read().strip())
    except (OSError, ValueError):
        return None, False

    return pid, _pid_exists(pid)


def _read_local_version(version_file: str) -> str | None:
    """Read the local broker version stamp when present."""
    if not os.path.exists(version_file):
        return None

    try:
        with open(version_file, encoding="utf-8") as handle:
            version = handle.read().strip()
    except OSError:
        return None

    return version or None


def _find_listener_pids_for_port(port: int | None) -> list[int]:
    """Return listener PIDs bound to a TCP port, or an empty list."""
    if port is None:
        return []

    try:
        result = subprocess.run(
            ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    pids: list[int] = []
    for raw in result.stdout.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        with contextlib.suppress(ValueError):
            pids.append(int(raw))
    return sorted(set(pids))


def _read_process_command(pid: int) -> str | None:
    """Return the command line for a PID when available."""
    try:
        command = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "command="],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return command or None


def collect_local_broker_diagnostics(runtime: TUIRuntimeConfig) -> LocalBrokerDiagnostics:
    """Collect PID/socket/version state from the local broker directory."""
    pid_file = str(runtime.pid_file)
    pid, pid_running = _read_local_pid(pid_file)
    version = _read_local_version(str(runtime.version_file))

    return LocalBrokerDiagnostics(
        pid_file=pid_file,
        pid_file_present=runtime.pid_file.exists(),
        pid=pid,
        pid_running=pid_running,
        socket_path=str(runtime.socket_path),
        socket_present=runtime.socket_path.exists(),
        version_file=str(runtime.version_file),
        version_file_present=runtime.version_file.exists(),
        version=version,
        version_mismatch=bool(version and version != __version__),
    )


def collect_dashboard_diagnostics(runtime: TUIRuntimeConfig) -> DashboardDiagnostics:
    """Probe the configured dashboard endpoint and any local listener ownership."""
    port = urlparse(runtime.base_url).port
    listener_pids = _find_listener_pids_for_port(port)
    listener_commands: dict[int, str] = {}
    for pid in listener_pids:
        command = _read_process_command(pid)
        if command is not None:
            listener_commands[pid] = command

    client = BrokerTUIClient(runtime)
    diagnostics = DashboardDiagnostics(
        base_url=runtime.base_url,
        port=port,
        listener_pids=listener_pids,
        listener_commands=listener_commands,
    )

    try:
        health_payload = client._request_json("/api/health")
    except RuntimeError as exc:
        diagnostics.health_error = str(exc)
    else:
        diagnostics.health_ok = health_payload.get("status") == "ok"
        if not diagnostics.health_ok:
            diagnostics.health_error = "GET /api/health returned a non-ok status."

    try:
        control, broker_status = client.probe_backend()
    except RuntimeError as exc:
        diagnostics.backend_error = str(exc)
    else:
        diagnostics.control = control
        diagnostics.broker_status = broker_status

    return diagnostics


def classify_doctor_report(
    runtime: TUIRuntimeConfig,
    local: LocalBrokerDiagnostics,
    dashboard: DashboardDiagnostics,
) -> DoctorReport:
    """Classify the current runtime into one actionable user-facing diagnosis."""
    python_runtime_lines = [
        f"Package Version: {__version__}",
        f"Python Executable: {sys.executable}",
        f"xcrun: {shutil.which('xcrun') or 'not found'}",
    ]
    local_state_lines = [
        f"PID File: {local.pid_file} ({'present' if local.pid_file_present else 'missing'})",
        "Daemon PID: "
        + (
            f"{local.pid} ({'running' if local.pid_running else 'not running'})"
            if local.pid is not None
            else "n/a"
        ),
        f"Socket: {local.socket_path} ({'present' if local.socket_present else 'missing'})",
        "Version File: "
        + f"{local.version_file} ({'present' if local.version_file_present else 'missing'})",
        f"Recorded Daemon Version: {local.version or 'n/a'}",
    ]
    if local.version_mismatch:
        local_state_lines.append(f"Version Mismatch: yes (package {__version__})")
    else:
        local_state_lines.append("Version Mismatch: no")

    dashboard_lines = [
        f"Endpoint: {dashboard.base_url}",
        f"Port: {dashboard.port if dashboard.port is not None else 'n/a'}",
        "Listener PIDs: " + (", ".join(str(pid) for pid in dashboard.listener_pids) or "none"),
        f"Health Check: {'ok' if dashboard.health_ok else 'unreachable'}",
    ]
    for pid, command in dashboard.listener_commands.items():
        dashboard_lines.append(f"Listener {pid}: {command}")
    if dashboard.service_name:
        dashboard_lines.append(f"Reported Service: {dashboard.service_name}")
    if dashboard.health_error:
        dashboard_lines.append(f"Health Detail: {dashboard.health_error}")
    if dashboard.backend_error:
        dashboard_lines.append(f"Backend Detail: {dashboard.backend_error}")

    broker_runtime_lines: list[str] = []
    evidence_lines: list[str] = []

    if local.version_mismatch and local.pid_running:
        return DoctorReport(
            code="version-mismatch",
            ok=False,
            summary=(
                "Running broker daemon version does not match this mcpbridge-wrapper installation."
            ),
            next_action=(
                "Restart the broker from this environment with "
                "`mcpbridge-wrapper --broker-stop && mcpbridge-wrapper --broker-console`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=[
                f"Daemon version file reports {local.version}, package version is {__version__}.",
            ],
        )

    if (
        local.pid_file_present
        and not local.pid_running
        and (local.socket_present or local.version_file_present)
    ):
        evidence_lines.append("PID file exists but does not point to a running broker process.")
        if local.socket_present:
            evidence_lines.append("Broker socket still exists on disk.")
        if local.version_file_present:
            evidence_lines.append("Broker version stamp still exists on disk.")
        return DoctorReport(
            code="stale-runtime",
            ok=False,
            summary=(
                "Broker state files are stale; no live broker process owns the current runtime."
            ),
            next_action=(
                "Clean up with `mcpbridge-wrapper --broker-stop`, then restart with "
                "`mcpbridge-wrapper --broker-console`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines,
        )

    if dashboard.broker_available and dashboard.broker_payload is not None:
        broker_payload = dashboard.broker_payload
        broker_runtime_lines = [
            f"State: {broker_payload.get('state', 'n/a')}",
            f"Daemon PID: {broker_payload.get('pid', 'n/a')}",
            f"Upstream PID: {broker_payload.get('upstream_pid', 'n/a')}",
            f"Upstream Alive: {'yes' if broker_payload.get('upstream_alive') else 'no'}",
            f"Initialized: {'yes' if broker_payload.get('upstream_initialized') else 'no'}",
            f"Connected Clients: {broker_payload.get('connected_clients', 'n/a')}",
            f"Reconnect Attempt: {broker_payload.get('reconnect_attempt', 'n/a')}",
        ]
        state = str(broker_payload.get("state") or "")
        upstream_alive = bool(broker_payload.get("upstream_alive"))
        upstream_initialized = bool(broker_payload.get("upstream_initialized"))

        if state == "ready" and upstream_alive and upstream_initialized:
            return DoctorReport(
                code="healthy",
                ok=True,
                summary="Broker daemon and broker-backed dashboard are healthy.",
                next_action=(
                    "Connect your MCP client with `--broker`, or use "
                    "`mcpbridge-wrapper --broker-console` for the attached frontend."
                ),
                exit_code=0,
                python_runtime_lines=python_runtime_lines,
                local_state_lines=local_state_lines,
                dashboard_lines=dashboard_lines,
                broker_runtime_lines=broker_runtime_lines,
                evidence_lines=["Dashboard is reachable and reports service `broker-daemon`."],
            )

        if not upstream_alive:
            evidence_lines.append(
                "The broker-backed dashboard is reachable, but the upstream "
                "Xcode bridge is not alive."
            )
        if not upstream_initialized:
            evidence_lines.append("The upstream initialize/tools probe has not completed yet.")
        if state and state != "ready":
            evidence_lines.append(f"Broker runtime state is `{state}`.")
        return DoctorReport(
            code="broker-degraded",
            ok=False,
            summary=(
                "Broker-backed dashboard is reachable, but the broker runtime is not fully ready."
            ),
            next_action=(
                "Keep Xcode open with Xcode Tools enabled and retry. If the state stays degraded, "
                "restart with `mcpbridge-wrapper --broker-console`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines,
        )

    if dashboard.service_name == "broker-daemon":
        status_error = None
        if isinstance(dashboard.broker_status, dict):
            raw_error = dashboard.broker_status.get("error")
            if isinstance(raw_error, str) and raw_error:
                status_error = raw_error
        if dashboard.backend_error:
            evidence_lines.append(dashboard.backend_error)
        if status_error:
            evidence_lines.append(status_error)
        return DoctorReport(
            code="broker-degraded",
            ok=False,
            summary=(
                "Broker-backed dashboard is reachable, but broker runtime status is unavailable."
            ),
            next_action=(
                "Retry after Xcode finishes any approval flow. If the runtime stays unavailable, "
                "restart with `mcpbridge-wrapper --broker-console`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines
            or ["Dashboard reports service `broker-daemon` but did not return runtime status."],
        )

    if dashboard.service_name and dashboard.service_name != "broker-daemon":
        evidence_lines.append(
            f"Endpoint reports service `{dashboard.service_name}` instead of `broker-daemon`."
        )
        if dashboard.listener_pids:
            evidence_lines.append(
                "Port owner PIDs: " + ", ".join(str(pid) for pid in dashboard.listener_pids)
            )
        return DoctorReport(
            code="wrong-service",
            ok=False,
            summary=(
                f"Dashboard endpoint {dashboard.base_url} is alive, "
                "but it is not the dedicated broker host."
            ),
            next_action=(
                "Stop the existing listener or retry startup with "
                "`mcpbridge-wrapper --broker-console --web-ui-restart`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines,
        )

    if dashboard.listener_pids and (dashboard.health_ok or dashboard.backend_error):
        evidence_lines.append(
            "A listener already owns the configured dashboard port, but it is "
            "not exposing broker-daemon."
        )
        if dashboard.backend_error:
            evidence_lines.append(dashboard.backend_error)
        return DoctorReport(
            code="port-occupied",
            ok=False,
            summary=f"Dashboard port {dashboard.port} is occupied by another listener.",
            next_action=(
                "Free the port or retry startup with "
                "`mcpbridge-wrapper --broker-console --web-ui-restart`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines,
        )

    if local.pid_running:
        if dashboard.health_error:
            evidence_lines.append(dashboard.health_error)
        if dashboard.backend_error:
            evidence_lines.append(dashboard.backend_error)
        return DoctorReport(
            code="broker-without-dashboard",
            ok=False,
            summary=(
                "Broker daemon is running, but no broker-backed dashboard is "
                f"reachable at {runtime.base_url}."
            ),
            next_action=(
                "Restart the dedicated host with "
                "`mcpbridge-wrapper --broker-stop && mcpbridge-wrapper --broker-console`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines or ["No reachable broker-backed dashboard was detected."],
        )

    if dashboard.listener_pids:
        evidence_lines.append(
            "A process is already listening on the configured dashboard port before broker startup."
        )
        return DoctorReport(
            code="port-occupied",
            ok=False,
            summary=f"Dashboard port {dashboard.port} is already occupied before broker startup.",
            next_action=(
                "Stop the existing listener or start again with "
                "`mcpbridge-wrapper --broker-console --web-ui-restart`."
            ),
            exit_code=1,
            python_runtime_lines=python_runtime_lines,
            local_state_lines=local_state_lines,
            dashboard_lines=dashboard_lines,
            broker_runtime_lines=broker_runtime_lines,
            evidence_lines=evidence_lines,
        )

    if dashboard.health_error:
        evidence_lines.append(dashboard.health_error)
    if dashboard.backend_error:
        evidence_lines.append(dashboard.backend_error)

    return DoctorReport(
        code="broker-not-running",
        ok=False,
        summary="No running broker daemon was detected.",
        next_action=(
            "Start the recommended dedicated host with `mcpbridge-wrapper --broker-console`."
        ),
        exit_code=1,
        python_runtime_lines=python_runtime_lines,
        local_state_lines=local_state_lines,
        dashboard_lines=dashboard_lines,
        broker_runtime_lines=broker_runtime_lines,
        evidence_lines=(
            evidence_lines or ["No live broker PID or broker-backed dashboard was found."]
        ),
    )


def collect_doctor_report(
    *,
    web_ui_port: int | None,
    web_ui_config: str | None,
) -> DoctorReport:
    """Collect and classify broker diagnostics for the configured endpoint."""
    runtime = build_tui_runtime(
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
    )
    local = collect_local_broker_diagnostics(runtime)
    dashboard = collect_dashboard_diagnostics(runtime)
    return classify_doctor_report(runtime, local, dashboard)


def render_doctor_report(report: DoctorReport) -> str:
    """Render a user-facing diagnostics report."""
    lines = [
        "mcpbridge-wrapper doctor",
        f"Status: {'OK' if report.ok else 'ISSUE'}",
        f"Summary: {report.summary}",
        f"Next Action: {report.next_action}",
        "",
        "Python Runtime",
        *[f"- {line}" for line in report.python_runtime_lines],
        "",
        "Local Broker State",
        *[f"- {line}" for line in report.local_state_lines],
        "",
        "Dashboard",
        *[f"- {line}" for line in report.dashboard_lines],
    ]

    if report.broker_runtime_lines:
        lines.extend(["", "Broker Runtime", *[f"- {line}" for line in report.broker_runtime_lines]])

    if report.evidence_lines:
        lines.extend(["", "Evidence", *[f"- {line}" for line in report.evidence_lines]])

    return "\n".join(lines)


def run_doctor(
    *,
    web_ui_port: int | None,
    web_ui_config: str | None,
) -> int:
    """Execute doctor mode and print the resulting report."""
    report = collect_doctor_report(
        web_ui_port=web_ui_port,
        web_ui_config=web_ui_config,
    )
    print(render_doctor_report(report))
    return report.exit_code
