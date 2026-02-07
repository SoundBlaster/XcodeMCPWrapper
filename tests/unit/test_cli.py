"""Unit tests for the CLI module."""

from unittest.mock import patch

from mcpbridge_wrapper.cli import main


class TestCliMain:
    """Tests for CLI main function."""

    @patch("mcpbridge_wrapper.cli.sys.stderr")
    def test_main_prints_version_and_usage(self, mock_stderr):
        """Test that main prints version and usage info."""
        result = main()

        assert result == 0
        # Check that stderr.write was called at least twice (version and usage)
        # The actual count may vary based on print behavior
        assert mock_stderr.write.call_count >= 2

    @patch("mcpbridge_wrapper.cli.main")
    def test_module_has_main_function(self, mock_main):
        """Test that the CLI module has a main function."""
        mock_main.return_value = 0

        # Import and check the module
        import mcpbridge_wrapper.cli as cli_module

        assert hasattr(cli_module, "main")
        assert callable(cli_module.main)
