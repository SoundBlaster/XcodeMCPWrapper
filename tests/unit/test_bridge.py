"""Unit tests for the bridge module."""

import io
import queue
import subprocess
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from mcpbridge_wrapper.bridge import (
    cleanup_bridge,
    create_bridge,
    forward_stdin,
    read_stdout,
    read_stdout_line,
    run_stdin_forwarder,
    run_stdout_reader,
)


class TestCreateBridge:
    """Tests for create_bridge function."""

    @patch("mcpbridge_wrapper.bridge.subprocess.Popen")
    @patch("mcpbridge_wrapper.bridge.sys.stderr")
    def test_create_bridge_basic(self, mock_stderr, mock_popen):
        """Test creating a bridge with default arguments."""
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_popen.return_value = mock_process

        result = create_bridge()

        mock_popen.assert_called_once_with(
            ["xcrun", "mcpbridge"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=mock_stderr,
            text=True,
            bufsize=1,
        )
        assert result == mock_process

    @patch("mcpbridge_wrapper.bridge.subprocess.Popen")
    @patch("mcpbridge_wrapper.bridge.sys.stderr")
    def test_create_bridge_with_args(self, mock_stderr, mock_popen):
        """Test creating a bridge with additional arguments."""
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_popen.return_value = mock_process

        result = create_bridge(["--help"])

        mock_popen.assert_called_once_with(
            ["xcrun", "mcpbridge", "--help"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=mock_stderr,
            text=True,
            bufsize=1,
        )
        assert result == mock_process

    @patch("mcpbridge_wrapper.bridge.subprocess.Popen")
    @patch("mcpbridge_wrapper.bridge.sys.stderr")
    def test_create_bridge_returns_popen_with_pipes(self, mock_stderr, mock_popen):
        """Test that returned Popen has stdin and stdout pipes configured."""
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_popen.return_value = mock_process

        result = create_bridge()

        # Verify Popen was called with PIPE for stdin and stdout
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs["stdin"] == subprocess.PIPE
        assert call_kwargs["stdout"] == subprocess.PIPE
        assert call_kwargs["stderr"] == mock_stderr
        assert call_kwargs["text"] is True
        assert call_kwargs["bufsize"] == 1


class TestForwardStdin:
    """Tests for forward_stdin function."""

    def test_forward_stdin_writes_line(self):
        """Test that forward_stdin writes a line to bridge stdin."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()

        forward_stdin(mock_bridge, '{"test": "data"}\n')

        mock_bridge.stdin.write.assert_called_once_with('{"test": "data"}\n')
        mock_bridge.stdin.flush.assert_called_once()

    def test_forward_stdin_handles_none_stdin(self):
        """Test that forward_stdin handles None stdin gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = None

        # Should not raise
        forward_stdin(mock_bridge, "test\n")


class TestReadStdoutLine:
    """Tests for read_stdout_line function."""

    def test_read_stdout_line_returns_line(self):
        """Test that read_stdout_line returns a line from stdout."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdout = MagicMock()
        mock_bridge.stdout.readline.return_value = '{"result": "ok"}\n'

        result = read_stdout_line(mock_bridge)

        assert result == '{"result": "ok"}\n'
        mock_bridge.stdout.readline.assert_called_once()

    def test_read_stdout_line_returns_none_on_eof(self):
        """Test that read_stdout_line returns None when stdout is None."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdout = None

        result = read_stdout_line(mock_bridge)

        assert result is None


class TestCleanupBridge:
    """Tests for cleanup_bridge function."""

    def test_cleanup_bridge_closes_stdin_and_waits(self):
        """Test that cleanup_bridge closes stdin and waits for process."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_bridge.returncode = 0

        result = cleanup_bridge(mock_bridge)

        mock_bridge.stdin.close.assert_called_once()
        mock_bridge.wait.assert_called_once()
        assert result == 0

    def test_cleanup_bridge_handles_none_stdin(self):
        """Test that cleanup_bridge handles None stdin gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = None
        mock_bridge.returncode = 1

        result = cleanup_bridge(mock_bridge)

        mock_bridge.wait.assert_called_once()
        assert result == 1


class TestRunStdinForwarder:
    """Tests for run_stdin_forwarder function."""

    @patch("mcpbridge_wrapper.bridge.sys.stdin")
    def test_forwarder_thread_is_daemon(self, mock_stdin):
        """Test that the forwarder thread is a daemon thread."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_stdin.__iter__ = MagicMock(return_value=iter([]))

        thread = run_stdin_forwarder(mock_bridge)

        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True
        thread.join(timeout=0.1)

    @patch("mcpbridge_wrapper.bridge.sys.stdin")
    def test_forwarder_writes_lines_to_bridge(self, mock_stdin):
        """Test that forwarder writes stdin lines to bridge."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_stdin.__iter__ = MagicMock(
            return_value=iter(['{"test": "data"}\n', "second line\n"])
        )

        thread = run_stdin_forwarder(mock_bridge)
        thread.join(timeout=0.1)

        assert mock_bridge.stdin.write.call_count == 2
        mock_bridge.stdin.write.assert_any_call('{"test": "data"}\n')
        mock_bridge.stdin.write.assert_any_call("second line\n")

    @patch("mcpbridge_wrapper.bridge.sys.stdin")
    def test_forwarder_flushes_after_each_write(self, mock_stdin):
        """Test that forwarder flushes after each write."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_stdin.__iter__ = MagicMock(return_value=iter(["line1\n", "line2\n"]))

        thread = run_stdin_forwarder(mock_bridge)
        thread.join(timeout=0.1)

        assert mock_bridge.stdin.flush.call_count == 2

    @patch("mcpbridge_wrapper.bridge.sys.stdin")
    def test_forwarder_handles_broken_pipe(self, mock_stdin):
        """Test that forwarder handles BrokenPipeError gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_bridge.stdin.write.side_effect = BrokenPipeError()
        mock_stdin.__iter__ = MagicMock(return_value=iter(["test line\n"]))

        # Should not raise exception
        thread = run_stdin_forwarder(mock_bridge)
        thread.join(timeout=0.1)

    @patch("mcpbridge_wrapper.bridge.sys.stdin")
    def test_forwarder_handles_oserror(self, mock_stdin):
        """Test that forwarder handles OSError gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdin = MagicMock()
        mock_bridge.stdin.write.side_effect = OSError("Pipe closed")
        mock_stdin.__iter__ = MagicMock(return_value=iter(["test line\n"]))

        # Should not raise exception
        thread = run_stdin_forwarder(mock_bridge)
        thread.join(timeout=0.1)


class TestReadStdout:
    """Tests for read_stdout generator function."""

    def test_read_stdout_yields_complete_lines(self):
        """Test that read_stdout yields complete lines ending with newline."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = [
            '{"result": "ok"}\n',
            "second line\n",
            "",  # EOF
        ]
        mock_bridge.stdout = mock_stdout

        lines = list(read_stdout(mock_bridge))

        assert len(lines) == 2
        assert lines[0] == '{"result": "ok"}\n'
        assert lines[1] == "second line\n"

    def test_read_stdout_handles_empty_stdout(self):
        """Test that read_stdout handles None stdout gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdout = None

        lines = list(read_stdout(mock_bridge))

        assert lines == []

    def test_read_stdout_stops_on_eof(self):
        """Test that read_stdout stops when EOF is reached."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = ["line1\n", "line2\n", ""]
        mock_bridge.stdout = mock_stdout

        lines = list(read_stdout(mock_bridge))

        assert len(lines) == 2
        assert mock_stdout.readline.call_count == 3  # Called until empty string

    def test_read_stdout_passes_unmodified(self):
        """Test that read_stdout passes lines through unmodified."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        test_lines = [
            '{"json": "data"}\n',
            "plain text\n",
            "special chars: äöü\n",
            "",  # EOF
        ]
        mock_stdout.readline.side_effect = test_lines
        mock_bridge.stdout = mock_stdout

        lines = list(read_stdout(mock_bridge))

        assert lines == test_lines[:-1]  # Exclude EOF marker

    def test_read_stdout_is_generator(self):
        """Test that read_stdout returns a generator."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = ["line\n", ""]
        mock_bridge.stdout = mock_stdout

        result = read_stdout(mock_bridge)

        # Should be a generator (not a list)
        import types

        assert isinstance(result, types.GeneratorType)
        # Consume the generator
        list(result)


class TestRunStdoutReader:
    """Tests for run_stdout_reader function."""

    def test_reader_returns_thread_and_queue(self):
        """Test that run_stdout_reader returns thread and queue."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = ["", ""]  # EOF immediately
        mock_bridge.stdout = mock_stdout

        thread, output_queue = run_stdout_reader(mock_bridge)

        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True
        assert isinstance(output_queue, queue.Queue)
        thread.join(timeout=0.1)

    def test_reader_puts_lines_in_queue(self):
        """Test that reader puts stdout lines into queue."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = [
            '{"result": "ok"}\n',
            "second line\n",
            "",  # EOF
        ]
        mock_bridge.stdout = mock_stdout

        thread, output_queue = run_stdout_reader(mock_bridge)
        thread.join(timeout=0.1)

        # Get lines from queue (should be lines then None sentinel)
        lines = []
        while True:
            try:
                line = output_queue.get(timeout=0.1)
                if line is None:
                    break
                lines.append(line)
            except queue.Empty:
                break

        assert len(lines) == 2
        assert lines[0] == '{"result": "ok"}\n'
        assert lines[1] == "second line\n"

    def test_reader_puts_none_sentinel_on_eof(self):
        """Test that reader puts None sentinel when EOF reached."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = ["line\n", ""]  # One line then EOF
        mock_bridge.stdout = mock_stdout

        thread, output_queue = run_stdout_reader(mock_bridge)
        thread.join(timeout=0.1)

        # First item should be the line
        assert output_queue.get(timeout=0.1) == "line\n"
        # Second item should be None sentinel
        assert output_queue.get(timeout=0.1) is None

    def test_reader_handles_none_stdout(self):
        """Test that reader handles None stdout gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_bridge.stdout = None

        thread, output_queue = run_stdout_reader(mock_bridge)
        thread.join(timeout=0.1)

        # Should get None sentinel immediately
        assert output_queue.get(timeout=0.1) is None

    def test_reader_handles_broken_pipe(self):
        """Test that reader handles BrokenPipeError gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = BrokenPipeError()
        mock_bridge.stdout = mock_stdout

        thread, output_queue = run_stdout_reader(mock_bridge)
        thread.join(timeout=0.1)

        # Should get None sentinel after error
        assert output_queue.get(timeout=0.1) is None

    def test_reader_is_daemon_thread(self):
        """Test that reader thread is a daemon thread."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_stdout = MagicMock()
        mock_stdout.readline.side_effect = [""]
        mock_bridge.stdout = mock_stdout

        thread, _ = run_stdout_reader(mock_bridge)

        assert thread.daemon is True
        thread.join(timeout=0.1)
