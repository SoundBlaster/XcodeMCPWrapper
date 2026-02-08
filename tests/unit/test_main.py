"""Unit tests for the __main__ module."""

import queue
import subprocess
import sys
from subprocess import Popen
from unittest.mock import MagicMock, patch

import pytest

from mcpbridge_wrapper.__main__ import main


class TestMain:
    """Tests for main function."""

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_creates_bridge_and_threads(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main creates bridge and starts daemon threads."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None  # Bridge is running
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader with empty queue (just None sentinel)
        mock_queue = queue.Queue()
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        mock_create.assert_called_once_with(None)
        mock_stdin_forwarder.assert_called_once_with(mock_bridge)
        mock_stdout_reader.assert_called_once_with(mock_bridge)
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_processes_and_forwards_lines(
        self, mock_stdout, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main processes lines and forwards to stdout."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader with test data
        mock_queue = queue.Queue()
        mock_queue.put('{"result": "ok"}\n')
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        # Verify processed output was written (may be transformed)
        assert mock_stdout.write.called
        mock_stdout.flush.assert_called()
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_handles_keyboard_interrupt(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main handles KeyboardInterrupt gracefully."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader that raises KeyboardInterrupt
        mock_queue = MagicMock()
        mock_queue.get.side_effect = KeyboardInterrupt()
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        mock_cleanup.assert_called_once_with(mock_bridge)
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_returns_bridge_exit_code(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main returns the bridge's exit code."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader with empty queue
        mock_queue = queue.Queue()
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 42

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        assert result == 42

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_passes_arguments_to_bridge(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main passes command-line arguments to bridge."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader
        mock_queue = queue.Queue()
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--help"],
        ):
            main()

        mock_create.assert_called_once_with(["--help"])

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_processes_response_line(
        self, mock_stdout, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main applies process_response_line transformation."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader with JSON that needs transformation
        mock_queue = queue.Queue()
        mock_queue.put('{"result": {"content": [{"type": "text", "text": "{}"}]}}\n')
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        # Verify output was written (transformed JSON with structuredContent)
        assert mock_stdout.write.called
        # Check that structuredContent was injected in one of the write calls
        write_calls = [str(call) for call in mock_stdout.write.call_args_list]
        combined = " ".join(write_calls)
        assert "structuredContent" in combined
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_passthrough_non_json(
        self, mock_stdout, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main passes through non-JSON lines unchanged."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        # Setup mock stdout reader with plain text
        mock_queue = queue.Queue()
        mock_queue.put("Plain text log line\n")
        mock_queue.put(None)  # EOF sentinel
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)

        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        # Verify plain text was passed through
        mock_stdout.write.assert_any_call("Plain text log line\n")
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_handles_bridge_start_failure(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main handles bridge process startup failure."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = 1  # Already exited with error
        mock_create.return_value = mock_bridge

        with patch("mcpbridge_wrapper.__main__.sys.stderr") as mock_stderr:
            with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
                result = main()

        assert result == 1
        # print() writes message and newline separately
        mock_stderr.write.assert_any_call("Error: Failed to start mcpbridge")
