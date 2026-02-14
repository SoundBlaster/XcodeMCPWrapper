"""Tests for __main__.py WebUI integration."""

import queue
from unittest.mock import MagicMock, patch

import pytest

from mcpbridge_wrapper.__main__ import (
    _extract_request_id,
    _extract_tool_name,
    _has_error,
    _parse_webui_args,
    main,
)


class TestParseWebUIArgs:
    """Test _parse_webui_args function."""

    def test_no_webui_args(self):
        """Test parsing with no web UI args."""
        args = ["--some-other-arg"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is False
        assert web_ui_only is False
        assert port is None
        assert config_path is None
        assert remaining == ["--some-other-arg"]

    def test_webui_flag(self):
        """Test parsing --web-ui flag."""
        args = ["--web-ui"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port is None
        assert config_path is None
        assert remaining == []

    def test_webui_port(self):
        """Test parsing --web-ui-port."""
        args = ["--web-ui", "--web-ui-port", "9090"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port == 9090
        assert config_path is None
        assert remaining == []

    def test_webui_port_equals(self):
        """Test parsing --web-ui-port=9090."""
        args = ["--web-ui", "--web-ui-port=9090"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port == 9090

    def test_webui_config(self):
        """Test parsing --web-ui-config."""
        args = ["--web-ui", "--web-ui-config", "/path/to/config.json"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port is None
        assert config_path == "/path/to/config.json"
        assert remaining == []

    def test_webui_config_equals(self):
        """Test parsing --web-ui-config=/path."""
        args = ["--web-ui", "--web-ui-config=/path/to/config.json"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui_only is False
        assert config_path == "/path/to/config.json"

    def test_bridge_args_preserved(self):
        """Test that bridge args are preserved."""
        args = ["--web-ui", "--web-ui-port", "9090", "--", "--bridge-arg"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port == 9090
        assert remaining == ["--", "--bridge-arg"]

    def test_all_flags_together(self):
        """Test all flags together."""
        args = [
            "--web-ui",
            "--web-ui-port",
            "9090",
            "--web-ui-config",
            "/config.json",
            "--bridge-arg",
        ]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is False
        assert port == 9090
        assert config_path == "/config.json"
        assert remaining == ["--bridge-arg"]

    def test_webui_only_enables_webui(self):
        """Test parsing --web-ui-only standalone mode."""
        args = ["--web-ui-only"]
        web_ui, web_ui_only, port, config_path, remaining = _parse_webui_args(args)
        assert web_ui is True
        assert web_ui_only is True
        assert port is None
        assert config_path is None
        assert remaining == []

    def test_webui_port_non_numeric_raises(self):
        """Test invalid non-numeric web UI port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid --web-ui-port value"):
            _parse_webui_args(["--web-ui", "--web-ui-port", "abc"])

    def test_webui_port_below_range_raises(self):
        """Test out-of-range low port raises ValueError."""
        with pytest.raises(ValueError, match="between 1 and 65535"):
            _parse_webui_args(["--web-ui", "--web-ui-port", "0"])

    def test_webui_port_above_range_raises(self):
        """Test out-of-range high port raises ValueError."""
        with pytest.raises(ValueError, match="between 1 and 65535"):
            _parse_webui_args(["--web-ui-port=70000"])


class TestExtractToolName:
    """Test _extract_tool_name function."""

    def test_extract_from_params_name(self):
        """Test extracting tool name from params.name (MCP tools/call format)."""
        line = '{"method": "tools/call", "params": {"name": "BuildProject"}, "id": 1}'
        assert _extract_tool_name(line) == "BuildProject"

    def test_extract_from_params_name_nested(self):
        """Test extracting tool name from nested params."""
        line = (
            '{"jsonrpc": "2.0", "method": "tools/call", '
            '"params": {"name": "XcodeRead", "arguments": {}}, "id": 5}'
        )
        assert _extract_tool_name(line) == "XcodeRead"

    def test_extract_from_method(self):
        """Test extracting tool name from method field."""
        line = '{"method": "XcodeRead", "id": 1}'
        assert _extract_tool_name(line) == "XcodeRead"

    def test_extract_from_result_name(self):
        """Test extracting tool name from result.name."""
        line = '{"result": {"name": "XcodeWrite"}, "id": 1}'
        assert _extract_tool_name(line) == "XcodeWrite"

    def test_extract_from_result_toolname(self):
        """Test extracting tool name from result.toolName."""
        line = '{"result": {"toolName": "BuildProject"}, "id": 1}'
        assert _extract_tool_name(line) == "BuildProject"

    def test_skip_initialize_in_params(self):
        """Test that initialize is skipped when in params."""
        line = '{"method": "tools/call", "params": {"name": "initialize"}, "id": 1}'
        # Should return None because initialize is filtered out
        assert _extract_tool_name(line) is None

    def test_skip_tools_list_in_params(self):
        """Test that tools/list is skipped when in params."""
        line = '{"method": "tools/call", "params": {"name": "tools/list"}, "id": 1}'
        # Should return None because tools/list is filtered out
        assert _extract_tool_name(line) is None

    def test_no_tool_found(self):
        """Test when no tool name is found."""
        line = '{"id": 1, "jsonrpc": "2.0"}'
        assert _extract_tool_name(line) is None

    def test_invalid_json(self):
        """Test with invalid JSON."""
        line = "not valid json"
        assert _extract_tool_name(line) is None

    def test_non_dict_json(self):
        """Test with non-dict JSON."""
        line = '["just", "an", "array"]'
        assert _extract_tool_name(line) is None


class TestExtractRequestId:
    """Test _extract_request_id function."""

    def test_extract_id(self):
        """Test extracting request ID."""
        line = '{"id": 123, "method": "XcodeRead"}'
        assert _extract_request_id(line) == "123"

    def test_extract_string_id(self):
        """Test extracting string request ID."""
        line = '{"id": "req-123", "method": "XcodeRead"}'
        assert _extract_request_id(line) == "req-123"

    def test_no_id(self):
        """Test when no ID is present."""
        line = '{"method": "XcodeRead"}'
        assert _extract_request_id(line) is None

    def test_invalid_json(self):
        """Test with invalid JSON."""
        line = "not valid json"
        assert _extract_request_id(line) is None


class TestHasError:
    """Test _has_error function."""

    def test_has_error_field(self):
        """Test detecting error field."""
        line = '{"id": 1, "error": {"code": -32600, "message": "error"}}'
        assert _has_error(line) is True

    def test_no_error(self):
        """Test when no error is present."""
        line = '{"id": 1, "result": {"content": []}}'
        assert _has_error(line) is False

    def test_invalid_json(self):
        """Test with invalid JSON."""
        line = "not valid json"
        assert _has_error(line) is False

    def test_non_dict_json(self):
        """Test with non-dict JSON."""
        line = '"just a string"'
        assert _has_error(line) is False


class TestMainWebUI:
    """Tests for main function with WebUI enabled."""

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_with_webui_missing_deps(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main handles missing webui dependencies."""
        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui"],
        ), patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                {} if "webui" in name else __builtins__.__import__(name, *args, **kwargs)
            ),
        ):
            result = main()

        assert result == 1

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_with_webui_enabled(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main works with webui enabled."""
        pytest.importorskip("fastapi")

        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put('{"method": "XcodeRead", "id": 1}')
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("sys.stderr") as mock_stderr:
            result = main()

        assert result == 0
        # Check that dashboard started message was printed
        write_calls = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "Web UI dashboard started" in write_calls

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_with_webui_custom_port(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main works with custom webui port."""
        pytest.importorskip("fastapi")

        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui", "--web-ui-port", "9090"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("sys.stderr") as mock_stderr:
            result = main()

        assert result == 0
        # Check that custom port is in the message
        write_calls = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert ":9090" in write_calls

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_with_webui_only_skips_bridge(self, mock_create):
        """Test standalone Web UI mode does not start bridge process."""
        pytest.importorskip("fastapi")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui-only"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("mcpbridge_wrapper.webui.server.run_server") as mock_run_server:
            result = main()

        assert result == 0
        mock_run_server.assert_called_once()
        mock_create.assert_not_called()

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_with_webui_only_custom_port(self, mock_create):
        """Test standalone Web UI mode honors custom port."""
        pytest.importorskip("fastapi")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui-only", "--web-ui-port", "9091"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("mcpbridge_wrapper.webui.server.run_server") as mock_run_server:
            result = main()

        assert result == 0
        mock_create.assert_not_called()
        args = mock_run_server.call_args[0]
        config = args[0]
        assert config.port == 9091

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_with_invalid_webui_port(self, mock_create):
        """Test main returns controlled error for invalid --web-ui-port."""
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui", "--web-ui-port", "not-a-number"],
        ), patch("mcpbridge_wrapper.__main__.sys.stderr") as mock_stderr:
            result = main()

        assert result == 2
        mock_create.assert_not_called()
        write_calls = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "Invalid --web-ui-port value" in write_calls


class TestPortCollisionHandling:
    """Tests for Web UI port collision detection and handling (BUG-T6)."""

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_occupied_port_in_bridge_mode_skips_webui(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """When the Web UI port is occupied in bridge+webui mode, Web UI is skipped and MCP
        bridge starts normally — no crash, no unhandled exception."""
        pytest.importorskip("fastapi")

        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_q = queue.Queue()
        mock_q.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_q)
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=False
        ) as mock_avail, patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread"
        ) as mock_thread, patch(
            "mcpbridge_wrapper.__main__.sys.stderr"
        ) as mock_stderr:
            result = main()

        # Port was checked
        mock_avail.assert_called_once()
        # Web UI thread was NOT started
        mock_thread.assert_not_called()
        # Bridge WAS started
        mock_create.assert_called_once()
        # Warning printed to stderr
        write_calls = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "already in use" in write_calls
        assert "Skipping Web UI" in write_calls
        # Return code is 0 (MCP session continued successfully)
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_occupied_port_in_webui_only_mode_exits_with_error(self, mock_create):
        """When the Web UI port is occupied in --web-ui-only mode, exit code 1 with clear
        stderr message — the dashboard is the only purpose so failure is fatal."""
        pytest.importorskip("fastapi")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui-only"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=False
        ) as mock_avail, patch(
            "mcpbridge_wrapper.webui.server.run_server"
        ) as mock_run, patch(
            "mcpbridge_wrapper.__main__.sys.stderr"
        ) as mock_stderr:
            result = main()

        mock_avail.assert_called_once()
        mock_run.assert_not_called()
        mock_create.assert_not_called()
        write_calls = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "already in use" in write_calls
        assert result == 1

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_free_port_starts_webui_normally(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """When the requested port is free, Web UI thread starts as before (no regression)."""
        pytest.importorskip("fastapi")

        mock_bridge = MagicMock()
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_q = queue.Queue()
        mock_q.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_q)
        mock_cleanup.return_value = 0

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui"],
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ) as mock_avail, patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread"
        ) as mock_thread:
            result = main()

        mock_avail.assert_called_once()
        mock_thread.assert_called_once()
        mock_create.assert_called_once()
        assert result == 0

    def test_is_port_available_returns_true_for_free_port(self):
        """is_port_available returns True when the port is not bound by anyone."""
        import socket

        from mcpbridge_wrapper.webui.server import is_port_available

        # Find a free port by binding temporarily and then releasing it.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]
        # Port is now released; should be available
        assert is_port_available("127.0.0.1", free_port) is True

    def test_is_port_available_returns_false_for_occupied_port(self):
        """is_port_available returns False when the port is already bound."""
        import socket

        from mcpbridge_wrapper.webui.server import is_port_available

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupier:
            occupier.bind(("127.0.0.1", 0))
            occupied_port = occupier.getsockname()[1]
            # Port is held; second bind should fail
            assert is_port_available("127.0.0.1", occupied_port) is False
