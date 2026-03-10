#!/usr/bin/env python3
"""Observe MCP startup behavior around the Xcode approval dialog."""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_COMMAND = ["xcrun", "mcpbridge"]
EOF_MARKER = object()


@dataclass(frozen=True)
class ScenarioStep:
    """One deterministic outbound MCP message."""

    name: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class Event:
    """One recorded harness event."""

    t_ms: int
    direction: str
    event: str
    summary: str
    payload: dict[str, Any] | None = None
    line: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable representation."""
        data: dict[str, Any] = {
            "t_ms": self.t_ms,
            "direction": self.direction,
            "event": self.event,
            "summary": self.summary,
        }
        if self.payload is not None:
            data["payload"] = self.payload
        if self.line is not None:
            data["line"] = self.line
        return data


def build_scenario(name: str) -> list[ScenarioStep]:
    """Return the ordered JSON-RPC sequence for a named scenario."""
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "xcode-approval-harness", "version": "1.0"},
        },
    }
    initialized = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }

    scenarios: dict[str, list[ScenarioStep]] = {
        "approval-probe": [
            ScenarioStep("initialize", initialize),
            ScenarioStep("initialized-notification", initialized),
            ScenarioStep(
                "tools-list",
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            ),
            ScenarioStep(
                "resources-list",
                {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
            ),
            ScenarioStep(
                "resources-templates-list",
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "resources/templates/list",
                    "params": {},
                },
            ),
            ScenarioStep(
                "prompts-list",
                {"jsonrpc": "2.0", "id": 5, "method": "prompts/list", "params": {}},
            ),
        ],
        "tools-only": [
            ScenarioStep("initialize", initialize),
            ScenarioStep("initialized-notification", initialized),
            ScenarioStep(
                "tools-list-1",
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            ),
            ScenarioStep(
                "tools-list-2",
                {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
            ),
            ScenarioStep(
                "tools-list-3",
                {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
            ),
        ],
    }
    try:
        return scenarios[name]
    except KeyError as exc:
        raise ValueError(f"Unknown scenario '{name}'.") from exc


def summarize_message(msg: dict[str, Any]) -> str:
    """Return a compact human-readable JSON-RPC summary."""
    method = msg.get("method")
    if isinstance(method, str):
        return method

    msg_id = msg.get("id")
    if "result" in msg:
        result = msg.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            return f"result#{msg_id} tools/list ({len(result['tools'])} tools)"
        return f"result#{msg_id}"

    if "error" in msg:
        error = msg.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            return f"error#{msg_id} ({code})"
        return f"error#{msg_id}"

    return f"message#{msg_id}"


def event_from_json_line(
    *,
    t_ms: int,
    direction: str,
    raw_line: str,
) -> Event:
    """Parse one JSON line into an Event with a stable summary."""
    line = raw_line.rstrip("\n")
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return Event(
            t_ms=t_ms,
            direction=direction,
            event="text",
            summary=f"{direction}-text",
            line=line,
        )

    if isinstance(payload, dict):
        return Event(
            t_ms=t_ms,
            direction=direction,
            event="jsonrpc",
            summary=summarize_message(payload),
            payload=payload,
            line=line,
        )

    return Event(
        t_ms=t_ms,
        direction=direction,
        event="json",
        summary=f"{direction}-json",
        payload={"value": payload},
        line=line,
    )


def format_event_pretty(event: Event) -> str:
    """Return a stable one-line human-readable event string."""
    return f"[{event.t_ms:>6} ms] {event.direction.upper():<4} {event.event:<7} {event.summary}"


def make_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Observe xcrun mcpbridge or wrapper behavior around Xcode approval."
    )
    parser.add_argument(
        "--scenario",
        default="approval-probe",
        choices=("approval-probe", "tools-only"),
        help="Named outbound message sequence to run.",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.25,
        help="Seconds to wait between outbound steps (default: 0.25).",
    )
    parser.add_argument(
        "--pause-before-step",
        default=None,
        help="Pause before sending the named step.",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.0,
        help="Seconds to pause before the selected step (default: 0).",
    )
    parser.add_argument(
        "--read-timeout",
        type=float,
        default=2.0,
        help="Idle-read timeout after each step in seconds (default: 2).",
    )
    parser.add_argument(
        "--final-read-timeout",
        type=float,
        default=5.0,
        help="Idle-read timeout after the last step in seconds (default: 5).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSONL path for recorded events.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print live event lines as they are recorded.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional command override after '--'. Defaults to 'xcrun mcpbridge'.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    args = make_parser().parse_args(argv)
    if args.step_delay < 0 or args.pause_seconds < 0 or args.read_timeout <= 0:
        raise SystemExit("step-delay, pause-seconds, and read-timeout must be positive.")
    if args.final_read_timeout <= 0:
        raise SystemExit("final-read-timeout must be positive.")
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    args.command = command or DEFAULT_COMMAND.copy()
    return args


class EventRecorder:
    """Collect and optionally persist recorded events."""

    def __init__(self, *, output_path: Path | None, pretty: bool) -> None:
        """Create a recorder with optional JSONL output and pretty-printing."""
        self.events: list[Event] = []
        self._output_path = output_path
        self._pretty = pretty
        self._output_file = None
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._output_file = output_path.open("w", encoding="utf-8")

    def close(self) -> None:
        """Close any open output file."""
        if self._output_file is not None:
            self._output_file.close()
            self._output_file = None

    def record(self, event: Event) -> None:
        """Append an event to memory, optional JSONL, and optional pretty output."""
        self.events.append(event)
        if self._output_file is not None:
            self._output_file.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
            self._output_file.flush()
        if self._pretty:
            print(format_event_pretty(event))


def _read_stream(
    stream: Any,
    stream_name: str,
    start_time: float,
    out_queue: queue.Queue[tuple[str, int, object]],
) -> None:
    """Read lines from one subprocess stream into a queue."""
    for raw_line in iter(stream.readline, ""):
        t_ms = int((time.monotonic() - start_time) * 1000)
        out_queue.put((stream_name, t_ms, raw_line))
    t_ms = int((time.monotonic() - start_time) * 1000)
    out_queue.put((stream_name, t_ms, EOF_MARKER))


def record_subprocess_events(
    recorder: EventRecorder,
    event_queue: queue.Queue[tuple[str, int, object]],
    start_time: float,
    idle_timeout: float,
) -> None:
    """Drain queued subprocess events until the queue is idle."""
    deadline = time.monotonic() + idle_timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            recorder.record(
                Event(
                    t_ms=int((time.monotonic() - start_time) * 1000),
                    direction="meta",
                    event="timeout",
                    summary=f"idle-timeout ({idle_timeout:.2f}s)",
                )
            )
            return
        try:
            stream_name, t_ms, raw = event_queue.get(timeout=remaining)
        except queue.Empty:
            recorder.record(
                Event(
                    t_ms=int((time.monotonic() - start_time) * 1000),
                    direction="meta",
                    event="timeout",
                    summary=f"idle-timeout ({idle_timeout:.2f}s)",
                )
            )
            return

        deadline = time.monotonic() + idle_timeout
        if raw is EOF_MARKER:
            recorder.record(
                Event(
                    t_ms=t_ms,
                    direction="meta",
                    event="eof",
                    summary=f"{stream_name}-eof",
                )
            )
            continue

        direction = "recv" if stream_name == "stdout" else "meta"
        recorder.record(event_from_json_line(t_ms=t_ms, direction=direction, raw_line=str(raw)))

        while True:
            try:
                stream_name, t_ms, raw = event_queue.get_nowait()
            except queue.Empty:
                break
            if raw is EOF_MARKER:
                recorder.record(
                    Event(
                        t_ms=t_ms,
                        direction="meta",
                        event="eof",
                        summary=f"{stream_name}-eof",
                    )
                )
                continue
            direction = "recv" if stream_name == "stdout" else "meta"
            recorder.record(event_from_json_line(t_ms=t_ms, direction=direction, raw_line=str(raw)))


def summarize_events(events: list[Event]) -> dict[str, Any]:
    """Build a compact verdict-oriented summary."""
    response_ids: list[int | str] = []
    tools_sizes: list[int] = []
    saw_tools_list_changed = False
    saw_stdout_eof = False
    timeout_count = 0

    for event in events:
        if event.event == "timeout":
            timeout_count += 1
        if event.event == "eof" and event.summary == "stdout-eof":
            saw_stdout_eof = True
        if event.payload is None or event.direction != "recv":
            continue
        payload = event.payload
        if payload.get("method") == "notifications/tools/list_changed":
            saw_tools_list_changed = True
        msg_id = payload.get("id")
        if msg_id is not None:
            response_ids.append(msg_id)
        result = payload.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            tools_sizes.append(len(result["tools"]))

    return {
        "events_recorded": len(events),
        "response_ids": response_ids,
        "tools_list_sizes": tools_sizes,
        "saw_non_empty_tools_list": any(size > 0 for size in tools_sizes),
        "saw_tools_list_changed": saw_tools_list_changed,
        "saw_stdout_eof": saw_stdout_eof,
        "timeout_count": timeout_count,
    }


def run_harness(args: argparse.Namespace) -> int:
    """Execute the configured scenario against the target command."""
    scenario = build_scenario(args.scenario)
    if args.pause_before_step is not None and args.pause_before_step not in {
        step.name for step in scenario
    }:
        raise SystemExit(f"Unknown step '{args.pause_before_step}' for scenario '{args.scenario}'.")

    start_time = time.monotonic()
    recorder = EventRecorder(output_path=args.output, pretty=args.pretty)
    event_queue: queue.Queue[tuple[str, int, object]] = queue.Queue()

    process = subprocess.Popen(
        args.command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    recorder.record(
        Event(
            t_ms=0,
            direction="meta",
            event="spawn",
            summary="process-started",
            payload={"command": args.command, "pid": process.pid, "scenario": args.scenario},
        )
    )

    threads = [
        threading.Thread(
            target=_read_stream,
            args=(process.stdout, "stdout", start_time, event_queue),
            daemon=True,
        ),
        threading.Thread(
            target=_read_stream,
            args=(process.stderr, "stderr", start_time, event_queue),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()

    try:
        for index, step in enumerate(scenario):
            if index > 0 and args.step_delay > 0:
                time.sleep(args.step_delay)

            if step.name == args.pause_before_step and args.pause_seconds > 0:
                recorder.record(
                    Event(
                        t_ms=int((time.monotonic() - start_time) * 1000),
                        direction="meta",
                        event="pause",
                        summary=f"pause-before {step.name} ({args.pause_seconds:.2f}s)",
                    )
                )
                time.sleep(args.pause_seconds)

            line = json.dumps(step.payload, separators=(",", ":"))
            assert process.stdin is not None
            process.stdin.write(line + "\n")
            process.stdin.flush()
            recorder.record(
                Event(
                    t_ms=int((time.monotonic() - start_time) * 1000),
                    direction="send",
                    event="jsonrpc",
                    summary=step.name,
                    payload=step.payload,
                    line=line,
                )
            )
            record_subprocess_events(recorder, event_queue, start_time, args.read_timeout)

        record_subprocess_events(recorder, event_queue, start_time, args.final_read_timeout)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
        recorder.record(
            Event(
                t_ms=int((time.monotonic() - start_time) * 1000),
                direction="meta",
                event="exit",
                summary=f"process-exit ({process.returncode})",
                payload={"returncode": process.returncode},
            )
        )
        recorder.close()

    summary = summarize_events(recorder.events)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.output is not None:
        print(f"Event log written to {args.output}")
    return 0 if process.returncode in (0, None, -15) else process.returncode


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    return run_harness(args)


if __name__ == "__main__":
    raise SystemExit(main())
