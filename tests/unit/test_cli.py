"""Unit tests for the cli module."""

from unittest.mock import patch

from mcpbridge_wrapper.cli import cli_main


class TestCliMain:
    """Tests for cli_main function."""

    def test_cli_main_calls_main(self):
        """Test that cli_main calls main from __main__."""
        with patch("mcpbridge_wrapper.cli.main") as mock_main:
            mock_main.return_value = 0
            result = cli_main()
            assert result == 0
            mock_main.assert_called_once()

    def test_cli_main_returns_exit_code(self):
        """Test that cli_main returns the exit code from main."""
        with patch("mcpbridge_wrapper.cli.main") as mock_main:
            mock_main.return_value = 1
            result = cli_main()
            assert result == 1
            mock_main.assert_called_once()
