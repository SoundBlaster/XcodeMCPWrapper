"""Unit tests for the CLI module."""

from unittest.mock import MagicMock, patch

from mcpbridge_wrapper.cli import main


class TestCliMain:
    """Tests for CLI main function."""

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_handles_bridge_creation(self, mock_create_bridge):
        """Test that main handles bridge creation and cleanup."""
        # Mock the bridge to avoid calling xcrun
        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_bridge.stdout.readline.return_value = ""
        mock_bridge.returncode = 0
        mock_create_bridge.return_value = mock_bridge

        with patch(
            "mcpbridge_wrapper.__main__.run_stdin_forwarder"
        ) as mock_stdin, patch(
            "mcpbridge_wrapper.__main__.run_stdout_reader"
        ) as mock_stdout:
            mock_queue = MagicMock()
            mock_queue.get.return_value = None  # EOF immediately
            mock_stdout.return_value = (MagicMock(), mock_queue)

            result = main()

        assert result == 0
        # Verify bridge was created
        mock_create_bridge.assert_called_once()

    def test_module_has_main_function(self):
        """Test that the CLI module has a main function."""
        # Import and check the module
        import mcpbridge_wrapper.cli as cli_module

        assert hasattr(cli_module, "main")
        assert callable(cli_module.main)
