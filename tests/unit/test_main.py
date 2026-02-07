"""Unit tests for the __main__ module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mcpbridge_wrapper.__main__ import main


class TestMain:
    """Tests for main function."""

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.read_stdout_line")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_creates_bridge_and_forwarder(
        self, mock_stdout, mock_read_line, mock_cleanup, mock_create, mock_run_forwarder
    ):
        """Test that main creates bridge and starts stdin forwarder."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_create.return_value = mock_bridge
        mock_read_line.return_value = None  # EOF immediately
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        mock_create.assert_called_once_with(None)
        mock_run_forwarder.assert_called_once_with(mock_bridge)
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.read_stdout_line")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_forwards_lines_to_stdout(
        self, mock_stdout, mock_read_line, mock_cleanup, mock_create, mock_run_forwarder
    ):
        """Test that main forwards bridge output to stdout."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_create.return_value = mock_bridge
        mock_read_line.side_effect = ['{"result": "ok"}\n', ""]  # One line then EOF
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        mock_stdout.write.assert_called_once_with('{"result": "ok"}\n')
        mock_stdout.flush.assert_called_once()
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.read_stdout_line")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_handles_keyboard_interrupt(
        self, mock_stdout, mock_read_line, mock_cleanup, mock_create, mock_run_forwarder
    ):
        """Test that main handles KeyboardInterrupt gracefully."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_create.return_value = mock_bridge
        mock_read_line.side_effect = KeyboardInterrupt()
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        mock_cleanup.assert_called_once_with(mock_bridge)
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.read_stdout_line")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_returns_bridge_exit_code(
        self, mock_stdout, mock_read_line, mock_cleanup, mock_create, mock_run_forwarder
    ):
        """Test that main returns the bridge's exit code."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_create.return_value = mock_bridge
        mock_read_line.return_value = None
        mock_cleanup.return_value = 42

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        assert result == 42

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.read_stdout_line")
    @patch("mcpbridge_wrapper.__main__.sys.stdout")
    def test_main_passes_arguments_to_bridge(
        self, mock_stdout, mock_read_line, mock_cleanup, mock_create, mock_run_forwarder
    ):
        """Test that main passes command-line arguments to bridge."""
        mock_bridge = MagicMock(spec=subprocess.Popen)
        mock_create.return_value = mock_bridge
        mock_read_line.return_value = None
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--help"],
        ):
            main()

        mock_create.assert_called_once_with(["--help"])
