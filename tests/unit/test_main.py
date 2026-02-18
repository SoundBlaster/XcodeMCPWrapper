"""Unit tests for the __main__ module."""

import queue
from subprocess import Popen
from unittest.mock import MagicMock, patch

from mcpbridge_wrapper.__main__ import main
from mcpbridge_wrapper.webui.config import WebUIConfig


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
        mock_stdin_forwarder.assert_called_once()
        # Check that bridge was passed (first positional arg)
        assert mock_stdin_forwarder.call_args[0][0] == mock_bridge
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

    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.signal.signal")
    def test_main_writes_missing_newline(
        self, mock_signal, mock_cleanup, mock_create, mock_stdout_reader
    ):
        """Test that main appends a newline when processed output lacks one."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        # A line without trailing newline
        mock_queue.put('{"result": "ok"}')
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        mock_stdout = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stdout", mock_stdout), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]
        ):
            result = main()

        # Should write the processed content, then an extra newline
        assert mock_stdout.write.call_count >= 2
        mock_stdout.write.assert_any_call("\n")
        mock_stdout.flush.assert_called()
        assert result == 0

    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_diagnostic_printed_when_tools_list_no_response(
        self, mock_cleanup, mock_create, mock_stdout_reader
    ):
        """Test diagnostic message is printed when initialize + tools/list are seen.

        The diagnostic should only be printed when exit_code == 0.
        """
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put('{"method":"initialize","id":1}\n')
        mock_queue.put('{"method":"tools/list","id":2}\n')
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        mock_stderr = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stderr", mock_stderr), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]
        ):
            result = main()

        assert result == 0
        # The diagnostic helper prints a multi-line message to stderr.
        combined = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "DIAGNOSTIC" in combined
        assert "Xcode Tools MCP" in combined

    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_diagnostic_not_printed_when_exit_code_nonzero(
        self, mock_cleanup, mock_create, mock_stdout_reader
    ):
        """Test diagnostic is not printed when exit_code is non-zero."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put('{"method":"initialize","id":1}\n')
        mock_queue.put('{"method":"tools/list","id":2}\n')
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 2

        mock_stderr = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stderr", mock_stderr), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]
        ):
            result = main()

        assert result == 2
        combined = " ".join(str(c) for c in mock_stderr.write.call_args_list)
        assert "DIAGNOSTIC" not in combined

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

        with patch("mcpbridge_wrapper.__main__.sys.stderr") as mock_stderr, patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]
        ):
            result = main()

        assert result == 1
        # print() writes message and newline separately
        mock_stderr.write.assert_any_call("Error: Failed to start mcpbridge")

    @patch("mcpbridge_wrapper.__main__.process_response_line", side_effect=lambda s, method=None: s)
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__._extract_request_id", return_value="req-1")
    @patch("mcpbridge_wrapper.__main__._extract_tool_name", return_value="BuildProject")
    @patch("mcpbridge_wrapper.__main__._has_error", return_value=False)
    def test_main_records_metrics_for_tracked_request_and_response(
        self,
        mock_has_error,
        mock_extract_tool_name,
        mock_extract_request_id,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        mock_process_response_line,
    ):
        """Test that metrics are recorded when a tracked request receives a response.

        The on_request handler is invoked as a side-effect of run_stdin_forwarder()
        being called from main(). To ensure the request is tracked *before* the
        response is processed, this test uses a custom stdout queue whose first
        get() call triggers on_request, and only then returns the response line.
        """
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_cleanup.return_value = 0

        metrics = MagicMock()

        captured_on_request = {}

        def _capture_forwarder(_bridge, on_request=None):
            captured_on_request["cb"] = on_request
            return MagicMock()

        mock_stdin_forwarder.side_effect = _capture_forwarder

        # Patch WebUI components so --web-ui does not start any real threads/servers.
        fake_webui_config = MagicMock(spec=WebUIConfig)
        fake_webui_config.host = "127.0.0.1"
        fake_webui_config.port = 8080
        fake_webui_config.audit_log_dir = "/tmp"
        fake_webui_config.audit_max_file_size_mb = 1
        fake_webui_config.audit_max_files = 1
        fake_webui_config.audit_enabled = False
        fake_webui_config.audit_capture_payload = False
        mock_webui_config_cls = MagicMock(spec=WebUIConfig, return_value=fake_webui_config)

        class _TriggeringQueue:
            def __init__(self, on_first_get):
                self._on_first_get = on_first_get
                self._count = 0

            def get(self):
                self._count += 1
                if self._count == 1:
                    # Ensure the on_request callback is registered before we trigger it.
                    assert "cb" in captured_on_request
                    self._on_first_get()
                    # After tracking request, return the response line.
                    return '{"jsonrpc":"2.0","id":"req-1","result":{"content":[]}}\n'
                return None

        with patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore",
            return_value=metrics,
        ), patch(
            "mcpbridge_wrapper.webui.audit.AuditLogger",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.webui.config.WebUIConfig",
            mock_webui_config_cls,
        ), patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.__main__.time.time",
            side_effect=[1000.0, 1000.123],
        ):

            def _track_request():
                captured_on_request["cb"](
                    '{"jsonrpc":"2.0","id":"req-1","method":"tools/call","params":{"name":"BuildProject"}}'
                )

            # Provide the stdout reader with a queue that triggers tracking before
            # yielding the response.
            mock_stdout_reader.return_value = (
                MagicMock(),
                _TriggeringQueue(_track_request),
            )

            with patch(
                "mcpbridge_wrapper.__main__.sys.argv",
                ["mcpbridge-wrapper", "--web-ui"],
            ):
                result = main()

        assert result == 0
        metrics.record_request.assert_called()
        metrics.record_response.assert_called()

    @patch("mcpbridge_wrapper.__main__.process_response_line", side_effect=lambda s, method=None: s)
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__._extract_tool_name", return_value="BuildProject")
    @patch("mcpbridge_wrapper.__main__._extract_request_id", return_value="req-2")
    def test_main_does_not_record_metrics_when_request_has_no_method(
        self,
        mock_extract_request_id,
        mock_extract_tool_name,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        mock_process_response_line,
    ):
        """Test that on_request ignores messages without a method field."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_cleanup.return_value = 0

        metrics = MagicMock()

        captured_on_request = {}

        def _capture_forwarder(_bridge, on_request=None):
            captured_on_request["cb"] = on_request
            return MagicMock()

        mock_stdin_forwarder.side_effect = _capture_forwarder

        fake_webui_config2 = MagicMock(spec=WebUIConfig)
        fake_webui_config2.host = "127.0.0.1"
        fake_webui_config2.port = 8080
        fake_webui_config2.audit_log_dir = "/tmp"
        fake_webui_config2.audit_max_file_size_mb = 1
        fake_webui_config2.audit_max_files = 1
        fake_webui_config2.audit_enabled = False
        fake_webui_config2.audit_capture_payload = False
        mock_webui_config_cls2 = MagicMock(spec=WebUIConfig, return_value=fake_webui_config2)

        with patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore",
            return_value=metrics,
        ), patch(
            "mcpbridge_wrapper.webui.audit.AuditLogger",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.webui.config.WebUIConfig",
            mock_webui_config_cls2,
        ), patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread",
            return_value=MagicMock(),
        ):
            mock_queue = queue.Queue()
            mock_queue.put(None)
            mock_stdout_reader.return_value = (MagicMock(), mock_queue)

            with patch(
                "mcpbridge_wrapper.__main__.sys.argv",
                ["mcpbridge-wrapper", "--web-ui"],
            ):
                main()

        assert "cb" in captured_on_request
        # Fire callback with JSON lacking "method"; MCPRequest.method will be None,
        # so it should not record.
        captured_on_request["cb"]('{"jsonrpc":"2.0","id":"req-2"}')

        metrics.record_request.assert_not_called()

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__.signal.signal")
    def test_main_sets_up_signal_handlers(
        self, mock_signal, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main sets up signal handlers for graceful shutdown."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            main()

        # Verify signal handlers were registered
        assert mock_signal.call_count == 2

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_tracks_initialize_method(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main tracks initialize method calls."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put('{"method": "initialize", "id": 1}\n')
        mock_queue.put(None)
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)
        mock_cleanup.return_value = 0

        mock_stdout = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stdout", mock_stdout), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]
        ):
            main()

        # Verify the line was processed and written
        mock_stdout.write.assert_any_call('{"method": "initialize", "id": 1}\n')

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_captures_client_info_from_initialize(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main extracts clientInfo from initialize and calls set_client_info."""
        from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore

        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)  # Immediate EOF - we test via on_request callback
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)
        mock_cleanup.return_value = 0

        captured_calls = []
        mock_metrics = MagicMock(spec=SharedMetricsStore)
        mock_metrics.set_client_info.side_effect = lambda n, v: captured_calls.append((n, v))

        # Simulate on_request directly: parse initialize line with clientInfo
        initialize_line = (
            '{"jsonrpc":"2.0","id":1,"method":"initialize",'
            '"params":{"clientInfo":{"name":"Cursor","version":"1.2.3"}}}\n'
        )

        # Capture the on_request callback passed to run_stdin_forwarder
        captured_on_request = []

        def capture_on_request(bridge, on_request=None):
            if on_request:
                captured_on_request.append(on_request)
            return MagicMock()

        mock_stdin_forwarder.side_effect = capture_on_request

        mock_stdout = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stdout", mock_stdout), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper", "--web-ui"]
        ), patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore", return_value=mock_metrics
        ), patch("mcpbridge_wrapper.webui.audit.AuditLogger"), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("mcpbridge_wrapper.webui.server.run_server_in_thread"):
            main()

        assert len(captured_on_request) == 1
        captured_on_request[0](initialize_line)
        assert ("Cursor", "1.2.3") in captured_calls

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_defaults_unknown_when_no_client_info(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that missing clientInfo in initialize defaults to 'unknown'."""
        from mcpbridge_wrapper.webui.shared_metrics import SharedMetricsStore

        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_thread = MagicMock()
        mock_stdout_reader.return_value = (mock_thread, mock_queue)
        mock_cleanup.return_value = 0

        captured_calls = []
        mock_metrics = MagicMock(spec=SharedMetricsStore)
        mock_metrics.set_client_info.side_effect = lambda n, v: captured_calls.append((n, v))

        # initialize without clientInfo
        initialize_line = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'

        captured_on_request = []

        def capture_on_request(bridge, on_request=None):
            if on_request:
                captured_on_request.append(on_request)
            return MagicMock()

        mock_stdin_forwarder.side_effect = capture_on_request

        mock_stdout = MagicMock()
        with patch("mcpbridge_wrapper.__main__.sys.stdout", mock_stdout), patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper", "--web-ui"]
        ), patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore", return_value=mock_metrics
        ), patch("mcpbridge_wrapper.webui.audit.AuditLogger"), patch(
            "mcpbridge_wrapper.webui.server.is_port_available", return_value=True
        ), patch("mcpbridge_wrapper.webui.server.run_server_in_thread"):
            main()

        assert len(captured_on_request) == 1
        captured_on_request[0](initialize_line)
        assert ("unknown", "unknown") in captured_calls


class TestParseErrorInfo:
    """Tests for _parse_error_info helper."""

    def test_no_error_response(self):
        from mcpbridge_wrapper.__main__ import _parse_error_info

        line = '{"jsonrpc":"2.0","id":1,"result":{"content":[]}}\n'
        is_error, code, message = _parse_error_info(line)
        assert is_error is False
        assert code is None
        assert message is None

    def test_error_response_with_code_and_message(self):
        from mcpbridge_wrapper.__main__ import _parse_error_info

        line = '{"jsonrpc":"2.0","id":1,"error":{"code":-32600,"message":"Invalid Request"}}\n'
        is_error, code, message = _parse_error_info(line)
        assert is_error is True
        assert code == -32600
        assert message == "Invalid Request"

    def test_invalid_json_returns_no_error(self):
        from mcpbridge_wrapper.__main__ import _parse_error_info

        line = "not valid json\n"
        is_error, code, message = _parse_error_info(line)
        assert is_error is False
        assert code is None
        assert message is None

    def test_has_error_delegates_to_parse_error_info(self):
        from mcpbridge_wrapper.__main__ import _has_error

        line = '{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}\n'
        assert _has_error(line) is True

    def test_has_error_false_for_success(self):
        from mcpbridge_wrapper.__main__ import _has_error

        line = '{"jsonrpc":"2.0","id":1,"result":{}}\n'
        assert _has_error(line) is False


class TestParseBrokerArgs:
    """Tests for _parse_broker_args helper."""

    def test_no_flags_returns_all_as_remaining(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        connect, spawn, remaining = _parse_broker_args(["--some-flag"])
        assert connect is False
        assert spawn is False
        assert remaining == ["--some-flag"]

    def test_broker_connect_flag(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        connect, spawn, remaining = _parse_broker_args(["--broker-connect"])
        assert connect is True
        assert spawn is False
        assert remaining == []

    def test_broker_spawn_implies_connect(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        connect, spawn, remaining = _parse_broker_args(["--broker-spawn"])
        assert connect is True
        assert spawn is True
        assert remaining == []


class TestMainBrokerMode:
    """Tests for main() broker proxy mode branch."""

    def test_main_broker_connect_success(self):
        """main() with --broker-connect runs proxy and returns 0."""
        argv = ["mcpbridge-wrapper", "--broker-connect"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run") as mock_run:
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()
            mock_run.return_value = None

            result = main()

        assert result == 0
        mock_run.assert_called_once()

    def test_main_broker_connect_timeout_returns_1(self):
        """main() with --broker-connect returns 1 on TimeoutError."""
        argv = ["mcpbridge-wrapper", "--broker-connect"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run", side_effect=TimeoutError("socket not found")):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()

            result = main()

        assert result == 1

    def test_main_broker_spawn_sets_auto_spawn(self):
        """main() with --broker-spawn constructs BrokerProxy(auto_spawn=True)."""
        argv = ["mcpbridge-wrapper", "--broker-spawn"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run") as mock_run:
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()
            mock_run.return_value = None

            result = main()

        assert result == 0
        _, kwargs = mock_proxy_cls.call_args
        assert kwargs.get("auto_spawn") is True

    def test_main_broker_connect_keyboard_interrupt_returns_0(self):
        """main() with --broker-connect returns 0 on KeyboardInterrupt."""
        argv = ["mcpbridge-wrapper", "--broker-connect"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run", side_effect=KeyboardInterrupt()):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()

            result = main()

        assert result == 0
