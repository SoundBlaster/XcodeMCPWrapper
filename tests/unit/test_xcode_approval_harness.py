#!/usr/bin/env python3
"""Tests for scripts/xcode_approval_harness.py."""

import argparse
import io
import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from xcode_approval_harness import (  # noqa: E402
    DEFAULT_PROTOCOL_VERSION,
    EOF_MARKER,
    Event,
    EventRecorder,
    build_scenario,
    event_from_json_line,
    format_event_pretty,
    parse_args,
    record_subprocess_events,
    run_harness,
    summarize_events,
)


class TestBuildScenario:
    """Scenario construction tests."""

    def test_approval_probe_contains_expected_methods(self) -> None:
        """The approval-probe scenario exercises the expected discovery methods."""
        steps = build_scenario("approval-probe")
        methods = [step.payload.get("method") for step in steps]
        initialize = steps[0].payload

        assert methods == [
            "initialize",
            "notifications/initialized",
            "tools/list",
            "resources/list",
            "resources/templates/list",
            "prompts/list",
        ]
        assert initialize["params"]["protocolVersion"] == DEFAULT_PROTOCOL_VERSION

    def test_tools_only_repeats_tools_list(self) -> None:
        """The tools-only scenario repeats tools/list after initialization."""
        steps = build_scenario("tools-only")
        assert [step.payload.get("method") for step in steps].count("tools/list") == 3

    def test_unknown_scenario_raises(self) -> None:
        """Unknown scenario names fail clearly."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            build_scenario("missing")


class TestEventParsing:
    """Event formatting and parsing tests."""

    def test_event_from_json_line_summarizes_tools_result(self) -> None:
        """tools/list result summaries include tool count."""
        line = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {"tools": [{"name": "XcodeRead"}, {"name": "XcodeWrite"}]},
            }
        )

        event = event_from_json_line(t_ms=125, direction="recv", raw_line=line)

        assert event.summary == "result#2 tools/list (2 tools)"
        assert event.payload is not None
        assert event.payload["result"]["tools"][0]["name"] == "XcodeRead"

    def test_event_from_json_line_keeps_text_when_not_json(self) -> None:
        """Non-JSON lines are preserved as text events."""
        event = event_from_json_line(t_ms=50, direction="meta", raw_line="stderr line")

        assert event.event == "text"
        assert event.summary == "meta-text"
        assert event.line == "stderr line"

    def test_format_event_pretty_is_stable(self) -> None:
        """Pretty format keeps columns stable for live observation."""
        pretty = format_event_pretty(
            Event(t_ms=42, direction="send", event="jsonrpc", summary="tools-list")
        )

        assert pretty == "[    42 ms] SEND jsonrpc tools-list"


class TestArgParsing:
    """CLI parsing and defaults."""

    def test_parse_args_uses_default_command(self) -> None:
        """Missing command override falls back to xcrun mcpbridge."""
        args = parse_args(["--scenario", "tools-only"])
        assert args.command == ["xcrun", "mcpbridge"]
        assert args.scenario == "tools-only"

    def test_parse_args_accepts_command_override_after_dash_dash(self) -> None:
        """A remainder command after '--' replaces the default target."""
        args = parse_args(["--pretty", "--", "uvx", "--from", "mcpbridge-wrapper"])
        assert args.command == ["uvx", "--from", "mcpbridge-wrapper"]
        assert args.pretty is True

    def test_parse_args_rejects_negative_read_timeout(self) -> None:
        """Timeout arguments must be positive."""
        with pytest.raises(SystemExit, match="read-timeout"):
            parse_args(["--read-timeout", "-1"])


class TestSummaries:
    """Aggregate summary extraction."""

    def test_summarize_events_detects_tools_catalog_and_list_changed(self) -> None:
        """Summary tracks both tool-catalog readiness and late list changes."""
        events = [
            Event(
                t_ms=0,
                direction="recv",
                event="jsonrpc",
                summary="result#2 tools/list (0 tools)",
                payload={"jsonrpc": "2.0", "id": 2, "result": {"tools": []}},
            ),
            Event(
                t_ms=100,
                direction="recv",
                event="jsonrpc",
                summary="notifications/tools/list_changed",
                payload={
                    "jsonrpc": "2.0",
                    "method": "notifications/tools/list_changed",
                    "params": {},
                },
            ),
            Event(
                t_ms=200,
                direction="recv",
                event="jsonrpc",
                summary="result#3 tools/list (20 tools)",
                payload={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {"tools": [{"name": "XcodeRead"} for _ in range(20)]},
                },
            ),
            Event(t_ms=300, direction="meta", event="eof", summary="stdout-eof"),
            Event(t_ms=400, direction="meta", event="timeout", summary="idle-timeout (2.00s)"),
        ]

        summary = summarize_events(events)

        assert summary["response_ids"] == [2, 3]
        assert summary["tools_list_sizes"] == [0, 20]
        assert summary["saw_non_empty_tools_list"] is True
        assert summary["saw_tools_list_changed"] is True
        assert summary["saw_stdout_eof"] is True
        assert summary["timeout_count"] == 1


class _BrokenPipeStdin:
    """Minimal stdin stub that fails on the first write."""

    def write(self, _data: str) -> None:
        raise BrokenPipeError("simulated broken pipe")

    def flush(self) -> None:
        return None


class _FakePopen:
    """Minimal subprocess stub for early child-exit tests."""

    def __init__(self) -> None:
        self.stdin = _BrokenPipeStdin()
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("mock startup failure\n")
        self.pid = 4242
        self.returncode = 7

    def poll(self) -> int:
        return self.returncode

    def terminate(self) -> None:
        return None

    def wait(self, timeout: Optional[float] = None) -> int:
        del timeout
        return self.returncode

    def kill(self) -> None:
        return None


class _DelayedStream:
    """Simple blocking stream that releases queued lines only after close()."""

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._closed = False
        self._condition = threading.Condition()

    def feed(self, *lines: str) -> None:
        with self._condition:
            self._lines.extend(lines)
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def readline(self) -> str:
        with self._condition:
            while not self._lines and not self._closed:
                self._condition.wait(timeout=0.1)
            if self._lines:
                return self._lines.pop(0)
            return ""


class _TerminatingBrokenPipePopen:
    """Process stub that emits stderr only during terminate/wait cleanup."""

    def __init__(self) -> None:
        self.stdin = _BrokenPipeStdin()
        self.stdout = _DelayedStream()
        self.stderr = _DelayedStream()
        self.pid = 4343
        self.returncode: Optional[int] = None

    def poll(self) -> Optional[int]:
        return self.returncode

    def terminate(self) -> None:
        self.returncode = 9
        self.stderr.feed("late shutdown stderr\n")
        self.stdout.close()
        self.stderr.close()

    def wait(self, timeout: Optional[float] = None) -> int:
        del timeout
        if self.returncode is None:
            time.sleep(0.01)
            self.terminate()
        return self.returncode or 0

    def kill(self) -> None:
        self.terminate()


class TestRunHarness:
    """Behavioral tests for the live harness runner."""

    def test_run_harness_records_write_failure_and_exits_cleanly(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Early child exit should produce a summary and a write-error event, not a traceback."""
        monkeypatch.setattr(
            "xcode_approval_harness.subprocess.Popen", lambda *args, **kwargs: _FakePopen()
        )

        output_path = tmp_path / "events.jsonl"
        args = argparse.Namespace(
            scenario="tools-only",
            pause_before_step=None,
            pause_seconds=0.0,
            step_delay=0.0,
            read_timeout=0.1,
            final_read_timeout=0.1,
            output=output_path,
            pretty=False,
            command=["fake-command"],
        )

        exit_code = run_harness(args)

        captured = capsys.readouterr()
        assert exit_code == 7
        assert '"events_recorded"' in captured.out
        assert "Traceback" not in captured.err

        events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
        assert any(event["event"] == "write-error" for event in events)
        assert any(event["event"] == "exit" for event in events)

    def test_run_harness_flushes_late_shutdown_events_before_exit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Late stderr/EOF queued during shutdown should be recorded before the exit event."""
        monkeypatch.setattr(
            "xcode_approval_harness.subprocess.Popen",
            lambda *args, **kwargs: _TerminatingBrokenPipePopen(),
        )

        output_path = tmp_path / "events.jsonl"
        args = argparse.Namespace(
            scenario="tools-only",
            pause_before_step=None,
            pause_seconds=0.0,
            step_delay=0.0,
            read_timeout=0.1,
            final_read_timeout=0.1,
            output=output_path,
            pretty=False,
            command=["fake-command"],
        )

        exit_code = run_harness(args)

        events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
        event_names = [event["event"] for event in events]
        summaries = [event["summary"] for event in events]
        assert exit_code == 9
        assert "meta-text" in summaries
        assert "stderr-eof" in summaries
        assert event_names.index("exit") > summaries.index("stderr-eof")


class TestRecordSubprocessEvents:
    """Direct queue-drain behavior."""

    def test_record_subprocess_events_returns_after_both_eof_without_timeout(self) -> None:
        """Two EOF markers should end the read loop without a synthetic idle-timeout."""
        recorder = EventRecorder(output_path=None, pretty=False)
        event_queue: queue.Queue[tuple[str, int, object]] = queue.Queue()
        event_queue.put(("stdout", 10, "ready\n"))
        event_queue.put(("stdout", 11, EOF_MARKER))
        event_queue.put(("stderr", 12, EOF_MARKER))

        record_subprocess_events(
            recorder,
            event_queue,
            start_time=time.monotonic(),
            idle_timeout=0.05,
        )

        summaries = [event.summary for event in recorder.events]
        assert "stdout-eof" in summaries
        assert "stderr-eof" in summaries
        assert not any(event.event == "timeout" for event in recorder.events)
