"""Unit tests for the __main__ module."""

import queue
import signal
from subprocess import Popen
from unittest.mock import ANY, MagicMock, patch

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
    def test_main_registers_stdin_closed_callback(
        self, mock_cleanup, mock_create, mock_stdout_reader, mock_stdin_forwarder
    ):
        """Test that main wires a stdin-closed callback into the forwarder."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        assert result == 0
        assert "on_stdin_closed" in mock_stdin_forwarder.call_args.kwargs
        assert callable(mock_stdin_forwarder.call_args.kwargs["on_stdin_closed"])

    @patch("mcpbridge_wrapper.__main__.terminate_bridge_process")
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_stdin_closed_callback_terminates_bridge_once(
        self,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        mock_terminate_bridge_process,
    ):
        """Test stdin-closed callback requests upstream shutdown exactly once."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_bridge.stdin = MagicMock()
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        assert result == 0
        on_stdin_closed = mock_stdin_forwarder.call_args.kwargs["on_stdin_closed"]
        on_stdin_closed()
        on_stdin_closed()

        mock_bridge.stdin.close.assert_called_once()
        mock_terminate_bridge_process.assert_called_once_with(mock_bridge, grace_period=5.0)

    @patch("mcpbridge_wrapper.__main__.time.sleep")
    @patch("mcpbridge_wrapper.__main__.time.monotonic", side_effect=[0.0, 0.0, 0.3])
    @patch("mcpbridge_wrapper.__main__.terminate_bridge_process")
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_stdin_closed_callback_briefly_drains_pending_methods(
        self,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        mock_terminate_bridge_process,
        _mock_monotonic,
        mock_sleep,
    ):
        """On stdin EOF, callback gives pending responses a short drain window."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_bridge.stdin = MagicMock()
        mock_create.return_value = mock_bridge

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)
        mock_cleanup.return_value = 0

        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
            result = main()

        assert result == 0
        on_request = mock_stdin_forwarder.call_args.kwargs["on_request"]
        on_stdin_closed = mock_stdin_forwarder.call_args.kwargs["on_stdin_closed"]

        # Track one pending request id so the callback enters the drain loop.
        on_request('{"jsonrpc":"2.0","id":"req-1","method":"resources/list"}\n')
        on_stdin_closed()

        mock_bridge.stdin.close.assert_called_once()
        assert mock_sleep.called
        mock_terminate_bridge_process.assert_called_once_with(mock_bridge, grace_period=5.0)

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

        def _capture_forwarder(_bridge, on_request=None, on_stdin_closed=None):
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

        def _capture_forwarder(_bridge, on_request=None, on_stdin_closed=None):
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

        def capture_on_request(bridge, on_request=None, on_stdin_closed=None):
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

        def capture_on_request(bridge, on_request=None, on_stdin_closed=None):
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


class TestPendingMethodTracking:
    """Tests for bounded pending method tracking."""

    def test_track_pending_method_caps_growth(self):
        """Map size is capped and oldest request IDs are evicted first."""
        from mcpbridge_wrapper.__main__ import _track_pending_method

        pending_methods = {}
        for i in range(8):
            _track_pending_method(
                pending_methods,
                request_id=f"req-{i}",
                method="resources/list",
                max_size=3,
            )

        assert len(pending_methods) == 3
        assert list(pending_methods.keys()) == ["req-5", "req-6", "req-7"]

    @patch("mcpbridge_wrapper.__main__.process_response_line", side_effect=lambda s, method=None: s)
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__._extract_request_id", side_effect=["req-1", "req-4"])
    def test_main_evicted_pending_method_falls_back_to_none(
        self,
        mock_extract_request_id,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        mock_process_response_line,
    ):
        """Oldest pending request loses method context when cap is exceeded."""
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_cleanup.return_value = 0

        captured_on_request = {}

        def _capture_forwarder(_bridge, on_request=None, on_stdin_closed=None):
            captured_on_request["cb"] = on_request
            return MagicMock()

        mock_stdin_forwarder.side_effect = _capture_forwarder

        class _TriggeringQueue:
            def __init__(self, on_first_get):
                self._on_first_get = on_first_get
                self._count = 0

            def get(self):
                self._count += 1
                if self._count == 1:
                    self._on_first_get()
                    return '{"jsonrpc":"2.0","id":"req-1","result":{"content":[]}}\n'
                if self._count == 2:
                    return '{"jsonrpc":"2.0","id":"req-4","result":{"content":[]}}\n'
                return None

        with patch("mcpbridge_wrapper.__main__.MAX_PENDING_METHODS", 3):

            def _prime_pending_methods():
                assert "cb" in captured_on_request
                for i in range(1, 5):
                    captured_on_request["cb"](
                        f'{{"jsonrpc":"2.0","id":"req-{i}","method":"resources/list"}}'
                    )

            mock_stdout_reader.return_value = (
                MagicMock(),
                _TriggeringQueue(_prime_pending_methods),
            )

            with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper"]):
                result = main()

        assert result == 0
        # req-1 is evicted; req-4 is retained.
        assert mock_process_response_line.call_args_list[0].kwargs["method"] is None
        assert mock_process_response_line.call_args_list[1].kwargs["method"] == "resources/list"


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

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(["--some-flag"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert status is False
        assert stop is False
        assert remaining == ["--some-flag"]

    def test_legacy_broker_connect_flag_is_forwarded(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(["--broker-connect"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--broker-connect"]

    def test_legacy_broker_spawn_flag_is_forwarded(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(["--broker-spawn"])
        assert daemon is False
        assert connect is False
        assert spawn is False
        assert remaining == ["--broker-spawn"]

    def test_broker_daemon_flag(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(["--broker-daemon"])
        assert daemon is True
        assert connect is False
        assert spawn is False
        assert remaining == []

    def test_broker_daemon_not_in_remaining(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(
            ["--broker-daemon", "--some-bridge-arg"]
        )
        assert daemon is True
        assert "--broker-daemon" not in remaining
        assert remaining == ["--some-bridge-arg"]

    def test_broker_flag_sets_spawn_and_connect(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(["--broker"])
        assert daemon is False
        assert connect is True
        assert spawn is True
        assert remaining == []

    def test_broker_flag_not_forwarded_to_bridge(self):
        from mcpbridge_wrapper.__main__ import _parse_broker_args

        daemon, connect, spawn, status, stop, remaining = _parse_broker_args(
            ["--broker", "--some-bridge-arg"]
        )
        assert "--broker" not in remaining
        assert remaining == ["--some-bridge-arg"]


class TestMainBrokerMode:
    """Tests for main() broker proxy mode branch."""

    def test_main_broker_flag_timeout_returns_1(self):
        """main() with --broker returns 1 on TimeoutError."""
        argv = ["mcpbridge-wrapper", "--broker"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run", side_effect=TimeoutError("socket not found")):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()

            result = main()

        assert result == 1

    def test_main_broker_flag_sets_auto_spawn(self):
        """main() with --broker constructs BrokerProxy(auto_spawn=True)."""
        argv = ["mcpbridge-wrapper", "--broker"]
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

    def test_main_broker_flag_success(self):
        """main() with --broker runs proxy and returns 0."""
        argv = ["mcpbridge-wrapper", "--broker"]
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

    def test_main_broker_flag_keyboard_interrupt_returns_0(self):
        """main() with --broker returns 0 on KeyboardInterrupt."""
        argv = ["mcpbridge-wrapper", "--broker"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run", side_effect=KeyboardInterrupt()):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()

            result = main()

        assert result == 0

    def test_main_broker_with_webui_propagates_spawn_args(self):
        """main() with --broker --web-ui passes web-ui args to proxy spawn."""
        argv = [
            "mcpbridge-wrapper",
            "--broker",
            "--web-ui",
            "--web-ui-restart",
            "--web-ui-port",
            "9090",
            "--web-ui-config",
            "/tmp/webui.json",
        ]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.proxy.BrokerProxy"
        ) as mock_proxy_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run"):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_proxy_cls.return_value = MagicMock()

            result = main()

        assert result == 0
        _, kwargs = mock_proxy_cls.call_args
        assert kwargs["auto_spawn"] is True
        assert kwargs["spawn_args"] == [
            "--broker-daemon",
            "--web-ui",
            "--web-ui-restart",
            "--web-ui-port",
            "9090",
            "--web-ui-config",
            "/tmp/webui.json",
        ]


class TestMainBrokerLifecycleCommands:
    """Tests for --broker-status and --broker-stop command branches."""

    @staticmethod
    def _make_config(tmp_path):
        from mcpbridge_wrapper.broker.types import BrokerConfig

        state_dir = tmp_path / "broker-state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return BrokerConfig(
            socket_path=state_dir / "broker.sock",
            pid_file=state_dir / "broker.pid",
            upstream_cmd=["xcrun", "mcpbridge"],
        )

    def test_main_broker_status_reports_running_pid_and_version_mismatch(self, tmp_path):
        cfg = self._make_config(tmp_path)
        cfg.pid_file.write_text("1234")
        cfg.version_file.write_text("0.0.1-old")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-status"],
        ), patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig.default",
            return_value=cfg,
        ), patch(
            "mcpbridge_wrapper.__main__.os.kill",
            return_value=None,
        ), patch(
            "mcpbridge_wrapper.__version__",
            "9.9.9",
        ), patch("builtins.print") as mock_print:
            result = main()

        assert result == 0
        printed = "\n".join(
            " ".join(str(arg) for arg in call.args) for call in mock_print.call_args_list
        )
        assert "Proxy version: 9.9.9" in printed
        assert "Daemon PID:    1234 (running)" in printed
        assert "WARNING: version mismatch! proxy=9.9.9, daemon=0.0.1-old" in printed

    def test_main_broker_stop_cleans_corrupt_pid_files(self, tmp_path):
        cfg = self._make_config(tmp_path)
        cfg.pid_file.write_text("not-a-number")
        cfg.socket_path.write_text("stale")
        cfg.version_file.write_text("old")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-stop"],
        ), patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig.default",
            return_value=cfg,
        ), patch("builtins.print") as mock_print:
            result = main()

        assert result == 0
        assert not cfg.pid_file.exists()
        assert not cfg.socket_path.exists()
        assert not cfg.version_file.exists()
        printed = "\n".join(
            " ".join(str(arg) for arg in call.args) for call in mock_print.call_args_list
        )
        assert "Corrupt PID file; cleaning up." in printed

    def test_main_broker_stop_permission_error_returns_1(self, tmp_path):
        cfg = self._make_config(tmp_path)
        cfg.pid_file.write_text("4321")

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-stop"],
        ), patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig.default",
            return_value=cfg,
        ), patch(
            "mcpbridge_wrapper.__main__.os.kill",
            side_effect=PermissionError,
        ), patch("builtins.print"):
            result = main()

        assert result == 1

    def test_main_broker_stop_successfully_terminates_and_cleans_files(self, tmp_path):
        cfg = self._make_config(tmp_path)
        cfg.pid_file.write_text("4321")
        cfg.socket_path.write_text("sock")
        cfg.version_file.write_text("ver")

        def fake_kill(pid, sig):
            assert pid == 4321
            if sig == signal.SIGTERM:
                return None
            raise ProcessLookupError

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-stop"],
        ), patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig.default",
            return_value=cfg,
        ), patch(
            "mcpbridge_wrapper.__main__.os.kill",
            side_effect=fake_kill,
        ), patch(
            "mcpbridge_wrapper.__main__.time.monotonic",
            side_effect=[100.0, 100.1],
        ), patch("builtins.print") as mock_print:
            result = main()

        assert result == 0
        assert not cfg.pid_file.exists()
        assert not cfg.socket_path.exists()
        assert not cfg.version_file.exists()
        printed = "\n".join(
            " ".join(str(arg) for arg in call.args) for call in mock_print.call_args_list
        )
        assert "Sent SIGTERM to broker (PID 4321)." in printed
        assert "Broker stopped and files cleaned up." in printed


class TestMainBrokerDaemonMode:
    """Tests for main() --broker-daemon mode."""

    def test_main_broker_daemon_returns_0_on_success(self):
        """main() with --broker-daemon runs daemon and returns 0."""
        argv = ["mcpbridge-wrapper", "--broker-daemon"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon"
        ) as mock_daemon_cls, patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer"
        ) as mock_transport_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run") as mock_run:
            mock_cfg_cls.default.return_value = MagicMock()
            mock_daemon_cls.return_value = MagicMock()
            mock_transport_cls.return_value = MagicMock()
            mock_run.return_value = None

            result = main()

        assert result == 0
        mock_run.assert_called_once()

    def test_main_broker_daemon_returns_0_on_keyboard_interrupt(self):
        """main() with --broker-daemon returns 0 on KeyboardInterrupt."""
        argv = ["mcpbridge-wrapper", "--broker-daemon"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon"
        ) as mock_daemon_cls, patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer"
        ) as mock_transport_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run", side_effect=KeyboardInterrupt()):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_daemon_cls.return_value = MagicMock()
            mock_transport_cls.return_value = MagicMock()

            result = main()

        assert result == 0

    def test_main_broker_daemon_returns_1_on_runtime_error(self):
        """main() with --broker-daemon returns 1 when RuntimeError raised."""
        argv = ["mcpbridge-wrapper", "--broker-daemon"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon"
        ) as mock_daemon_cls, patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer"
        ) as mock_transport_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch(
            "asyncio.run", side_effect=RuntimeError("Broker already running (PID 1234).")
        ):
            mock_cfg_cls.default.return_value = MagicMock()
            mock_daemon_cls.return_value = MagicMock()
            mock_transport_cls.return_value = MagicMock()

            result = main()

        assert result == 1

    def test_main_broker_daemon_does_not_start_bridge(self):
        """main() with --broker-daemon exits before launching xcrun mcpbridge."""
        argv = ["mcpbridge-wrapper", "--broker-daemon"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon"
        ) as mock_daemon_cls, patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer"
        ) as mock_transport_cls, patch(
            "mcpbridge_wrapper.broker.types.BrokerConfig"
        ) as mock_cfg_cls, patch("asyncio.run"), patch(
            "mcpbridge_wrapper.__main__.create_bridge"
        ) as mock_create_bridge:
            mock_cfg_cls.default.return_value = MagicMock()
            mock_daemon_cls.return_value = MagicMock()
            mock_transport_cls.return_value = MagicMock()

            main()

        mock_create_bridge.assert_not_called()

    def test_main_broker_daemon_wires_transport_to_daemon(self):
        """main() with --broker-daemon sets daemon._transport before asyncio.run."""
        argv = ["mcpbridge-wrapper", "--broker-daemon"]
        wired_transport = None

        def capture_run(coro):
            nonlocal wired_transport
            wired_transport = mock_daemon.return_value._transport

        mock_daemon = MagicMock()
        mock_transport = MagicMock()

        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon", mock_daemon
        ), patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer",
            return_value=mock_transport,
        ), patch("mcpbridge_wrapper.broker.types.BrokerConfig") as mock_cfg_cls, patch(
            "asyncio.run", side_effect=capture_run
        ):
            mock_cfg_cls.default.return_value = MagicMock()

            main()

        assert wired_transport is mock_transport

    def test_main_broker_daemon_webui_wires_metrics_and_audit_into_transport(self):
        """Broker daemon with --web-ui injects webui telemetry deps into transport."""
        argv = ["mcpbridge-wrapper", "--broker-daemon", "--web-ui"]
        broker_cfg = MagicMock()
        daemon = MagicMock()
        transport = MagicMock()
        webui_config = MagicMock(spec=WebUIConfig)
        webui_config.host = "127.0.0.1"
        webui_config.port = 8080
        metrics = MagicMock()
        audit = MagicMock()
        is_port_available = MagicMock(return_value=True)
        run_server = MagicMock()
        run_server_in_thread = MagicMock(return_value=MagicMock())

        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.__main__._prepare_webui_runtime",
            return_value=(
                webui_config,
                metrics,
                audit,
                is_port_available,
                run_server,
                run_server_in_thread,
            ),
        ), patch("mcpbridge_wrapper.broker.types.BrokerConfig") as mock_cfg_cls, patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon",
            return_value=daemon,
        ), patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer",
            return_value=transport,
        ) as mock_transport_cls, patch("asyncio.run"):
            mock_cfg_cls.default.return_value = broker_cfg

            result = main()

        assert result == 0
        run_server_in_thread.assert_called_once_with(
            webui_config,
            metrics,
            audit,
            service_name="broker-daemon",
            request_stop=ANY,
        )
        request_stop = run_server_in_thread.call_args.kwargs["request_stop"]
        request_stop()
        daemon.request_shutdown.assert_called_once_with()
        mock_transport_cls.assert_called_once_with(
            broker_cfg,
            daemon,
            metrics=metrics,
            audit=audit,
        )
        audit.close.assert_called_once_with()


class TestMainWebUIBrokerFlagCompatibility:
    """Validation for incompatible broker + web-ui-only combinations."""

    def test_main_rejects_webui_only_with_broker_daemon(self):
        argv = ["mcpbridge-wrapper", "--web-ui-only", "--broker-daemon"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.__main__.create_bridge"
        ) as mock_create:
            result = main()

        assert result == 2
        mock_create.assert_not_called()

    def test_main_rejects_webui_only_with_broker_flag(self):
        argv = ["mcpbridge-wrapper", "--web-ui-only", "--broker"]
        with patch("mcpbridge_wrapper.__main__.sys.argv", argv), patch(
            "mcpbridge_wrapper.__main__.create_bridge"
        ) as mock_create:
            result = main()

        assert result == 2
        mock_create.assert_not_called()


class TestParseWebUIArgs:
    """Tests for _parse_webui_args helper."""

    def test_parse_webui_restart_sets_flags_and_keeps_remaining(self):
        from mcpbridge_wrapper.__main__ import _parse_webui_args

        enabled, only, restart, port, config_path, remaining = _parse_webui_args(
            ["--web-ui-restart", "--web-ui-port", "9090", "--foo"]
        )
        assert enabled is True
        assert only is False
        assert restart is True
        assert port == 9090
        assert config_path is None
        assert remaining == ["--foo"]


class TestMainHelperCoverage:
    """Additional helper coverage for broker/web-ui orchestration."""

    def test_track_pending_method_with_non_positive_cap_is_noop(self):
        from mcpbridge_wrapper.__main__ import _track_pending_method

        pending = {"a": "tools/list"}
        _track_pending_method(pending, request_id="b", method="tools/call", max_size=0)
        assert pending == {"a": "tools/list"}

    def test_track_pending_method_reseen_id_moves_to_tail(self):
        from mcpbridge_wrapper.__main__ import _track_pending_method

        pending = {"a": "tools/list", "b": "tools/call"}
        _track_pending_method(pending, request_id="a", method="resources/list", max_size=2)
        assert list(pending.keys()) == ["b", "a"]
        assert pending["a"] == "resources/list"

    def test_build_broker_spawn_args_without_webui(self):
        from mcpbridge_wrapper.__main__ import _build_broker_spawn_args

        args = _build_broker_spawn_args(
            web_ui_enabled=False,
            web_ui_port=9090,
            web_ui_config="/tmp/webui.json",
            web_ui_restart=True,
        )
        assert args == ["--broker-daemon"]

    def test_build_broker_spawn_args_with_all_webui_flags(self):
        from mcpbridge_wrapper.__main__ import _build_broker_spawn_args

        args = _build_broker_spawn_args(
            web_ui_enabled=True,
            web_ui_port=9090,
            web_ui_config="/tmp/webui.json",
            web_ui_restart=True,
        )
        assert args == [
            "--broker-daemon",
            "--web-ui",
            "--web-ui-restart",
            "--web-ui-port",
            "9090",
            "--web-ui-config",
            "/tmp/webui.json",
        ]


class TestWebUIRestartHelpers:
    """Tests for Web UI restart port recovery helpers."""

    @patch("mcpbridge_wrapper.__main__.subprocess.run")
    def test_find_listener_pids_for_port_parses_numeric_lines(self, mock_run):
        from mcpbridge_wrapper.__main__ import _find_listener_pids_for_port

        mock_run.return_value = MagicMock(stdout="123\nabc\n456\n")
        assert _find_listener_pids_for_port(8080) == {123, 456}

    @patch("mcpbridge_wrapper.__main__.time.sleep")
    @patch("mcpbridge_wrapper.__main__.time.monotonic")
    @patch("mcpbridge_wrapper.__main__._pid_exists")
    @patch("mcpbridge_wrapper.__main__.os.kill")
    def test_terminate_pids_gracefully_then_force_sends_sigkill_after_timeout(
        self,
        mock_kill,
        mock_pid_exists,
        mock_monotonic,
        _mock_sleep,
    ):
        from mcpbridge_wrapper.__main__ import _terminate_pids_gracefully_then_force

        # First loop check before deadline sees process alive; second check after
        # SIGKILL sees process gone.
        mock_monotonic.side_effect = [0.0, 0.2, 2.0]
        mock_pid_exists.side_effect = [True, False]

        ok = _terminate_pids_gracefully_then_force({999}, grace_timeout_seconds=1.0)

        assert ok is True
        assert mock_kill.call_args_list[0].args[1] == signal.SIGTERM
        assert mock_kill.call_args_list[1].args[1] == signal.SIGKILL

    @patch("mcpbridge_wrapper.__main__._find_listener_pids_for_port", return_value={1111})
    @patch("mcpbridge_wrapper.__main__._terminate_pids_gracefully_then_force", return_value=True)
    def test_restart_webui_listener_uses_termination_flow(self, mock_terminate, mock_find):
        from mcpbridge_wrapper.__main__ import _restart_webui_listener

        assert _restart_webui_listener("127.0.0.1", 8080) is True
        mock_find.assert_called_once_with(8080)
        mock_terminate.assert_called_once_with({1111})


class TestMainWebUIRestartMode:
    """Tests for main() behavior with --web-ui-restart."""

    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    @patch("mcpbridge_wrapper.__main__._restart_webui_listener", return_value=True)
    def test_main_webui_restart_calls_restart_helper(
        self,
        mock_restart,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
    ):
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_cleanup.return_value = 0

        fake_webui_config = MagicMock(spec=WebUIConfig)
        fake_webui_config.host = "127.0.0.1"
        fake_webui_config.port = 8080
        fake_webui_config.audit_log_dir = "/tmp"
        fake_webui_config.audit_max_file_size_mb = 1
        fake_webui_config.audit_max_files = 1
        fake_webui_config.audit_enabled = False
        fake_webui_config.audit_capture_payload = False

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)

        with patch(
            "mcpbridge_wrapper.webui.config.WebUIConfig",
            return_value=fake_webui_config,
        ), patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.webui.audit.AuditLogger",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available",
            return_value=True,
        ), patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui", "--web-ui-restart"],
        ):
            result = main()

        assert result == 0
        mock_restart.assert_called_once_with("127.0.0.1", 8080)

    @patch("mcpbridge_wrapper.__main__._restart_webui_listener", return_value=False)
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_webui_restart_returns_1_when_port_cannot_be_freed(
        self, mock_create, _mock_restart
    ):
        fake_webui_config = MagicMock(spec=WebUIConfig)
        fake_webui_config.host = "127.0.0.1"
        fake_webui_config.port = 8080
        fake_webui_config.audit_log_dir = "/tmp"
        fake_webui_config.audit_max_file_size_mb = 1
        fake_webui_config.audit_max_files = 1
        fake_webui_config.audit_enabled = False
        fake_webui_config.audit_capture_payload = False

        with patch(
            "mcpbridge_wrapper.webui.config.WebUIConfig",
            return_value=fake_webui_config,
        ), patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui-only", "--web-ui-restart"],
        ):
            result = main()

        assert result == 1
        mock_create.assert_not_called()


class TestMainBrokerWebUIFlowCoverage:
    """Coverage for broker-daemon + web-ui orchestration branches."""

    def test_main_broker_daemon_webui_runtime_failure_returns_1(self):
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-daemon", "--web-ui"],
        ), patch("mcpbridge_wrapper.__main__._prepare_webui_runtime", return_value=None), patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon"
        ) as mock_daemon_cls:
            result = main()

        assert result == 1
        mock_daemon_cls.assert_not_called()

    def test_main_broker_daemon_webui_port_occupied_skips_dashboard_thread(self):
        broker_cfg = MagicMock()
        daemon = MagicMock()
        transport = MagicMock()
        webui_config = MagicMock(spec=WebUIConfig)
        webui_config.host = "127.0.0.1"
        webui_config.port = 8080
        metrics = MagicMock()
        audit = MagicMock()
        is_port_available = MagicMock(return_value=False)
        run_server = MagicMock()
        run_server_in_thread = MagicMock()

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-daemon", "--web-ui"],
        ), patch(
            "mcpbridge_wrapper.__main__._prepare_webui_runtime",
            return_value=(
                webui_config,
                metrics,
                audit,
                is_port_available,
                run_server,
                run_server_in_thread,
            ),
        ), patch("mcpbridge_wrapper.broker.types.BrokerConfig") as mock_cfg_cls, patch(
            "mcpbridge_wrapper.broker.daemon.BrokerDaemon", return_value=daemon
        ), patch(
            "mcpbridge_wrapper.broker.transport.UnixSocketServer",
            return_value=transport,
        ), patch("asyncio.run"):
            mock_cfg_cls.default.return_value = broker_cfg
            result = main()

        assert result == 0
        run_server_in_thread.assert_not_called()
        audit.close.assert_called_once_with()


class TestMainWebUIOnlyCoverage:
    """Additional direct-mode web-ui-only branches."""

    @patch("mcpbridge_wrapper.__main__.create_bridge")
    def test_main_webui_only_keyboard_interrupt_returns_0(self, mock_create):
        webui_config = MagicMock(spec=WebUIConfig)
        webui_config.host = "127.0.0.1"
        webui_config.port = 8080
        metrics = MagicMock()
        audit = MagicMock()
        is_port_available = MagicMock(return_value=True)
        run_server = MagicMock(side_effect=KeyboardInterrupt())
        run_server_in_thread = MagicMock()

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--web-ui-only"],
        ), patch(
            "mcpbridge_wrapper.__main__._prepare_webui_runtime",
            return_value=(
                webui_config,
                metrics,
                audit,
                is_port_available,
                run_server,
                run_server_in_thread,
            ),
        ):
            result = main()

        assert result == 0
        mock_create.assert_not_called()
        audit.close.assert_called_once_with()


class TestMainCaptureParamsCoverage:
    """Ensure capture_params branch records parameter key analytics."""

    @patch("mcpbridge_wrapper.__main__.process_response_line", side_effect=lambda s, method=None: s)
    @patch("mcpbridge_wrapper.__main__.run_stdin_forwarder")
    @patch("mcpbridge_wrapper.__main__.run_stdout_reader")
    @patch("mcpbridge_wrapper.__main__.create_bridge")
    @patch("mcpbridge_wrapper.__main__.cleanup_bridge")
    def test_main_records_param_keys_when_capture_params_enabled(
        self,
        mock_cleanup,
        mock_create,
        mock_stdout_reader,
        mock_stdin_forwarder,
        _mock_process_response_line,
    ):
        mock_bridge = MagicMock(spec=Popen)
        mock_bridge.poll.return_value = None
        mock_create.return_value = mock_bridge
        mock_cleanup.return_value = 0

        metrics = MagicMock()
        captured_on_request = {}

        def _capture_forwarder(_bridge, on_request=None, on_stdin_closed=None):
            captured_on_request["cb"] = on_request
            return MagicMock()

        mock_stdin_forwarder.side_effect = _capture_forwarder

        fake_webui_config = MagicMock(spec=WebUIConfig)
        fake_webui_config.host = "127.0.0.1"
        fake_webui_config.port = 8080
        fake_webui_config.capture_params = True
        fake_webui_config.audit_log_dir = "/tmp"
        fake_webui_config.audit_max_file_size_mb = 1
        fake_webui_config.audit_max_files = 1
        fake_webui_config.audit_enabled = False
        fake_webui_config.audit_capture_payload = False

        mock_queue = queue.Queue()
        mock_queue.put(None)
        mock_stdout_reader.return_value = (MagicMock(), mock_queue)

        with patch(
            "mcpbridge_wrapper.webui.shared_metrics.SharedMetricsStore",
            return_value=metrics,
        ), patch(
            "mcpbridge_wrapper.webui.audit.AuditLogger",
            return_value=MagicMock(),
        ), patch(
            "mcpbridge_wrapper.webui.config.WebUIConfig",
            return_value=fake_webui_config,
        ), patch(
            "mcpbridge_wrapper.webui.server.is_port_available",
            return_value=True,
        ), patch(
            "mcpbridge_wrapper.webui.server.run_server_in_thread",
            return_value=MagicMock(),
        ), patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper", "--web-ui"]):
            result = main()

        assert result == 0
        captured_on_request["cb"](
            '{"jsonrpc":"2.0","id":"req-99","method":"tools/call",'
            '"params":{"name":"BuildProject","arguments":{"tabIdentifier":"windowtab1","scheme":"App"}}}'
        )
        metrics.record_param_keys.assert_called_once_with(
            "BuildProject",
            ["tabIdentifier", "scheme"],
        )


class TestMainWebUIRestartCoverageHelpers:
    """Additional helper coverage for restart primitives in __main__."""

    @patch("mcpbridge_wrapper.__main__.subprocess.run", side_effect=OSError("missing lsof"))
    def test_find_listener_pids_handles_oserror(self, _mock_run):
        from mcpbridge_wrapper.__main__ import _find_listener_pids_for_port

        assert _find_listener_pids_for_port(8080) == set()

    @patch("mcpbridge_wrapper.__main__.subprocess.run")
    def test_find_listener_pids_skips_blank_lines(self, mock_run):
        from mcpbridge_wrapper.__main__ import _find_listener_pids_for_port

        mock_run.return_value = MagicMock(stdout="\n123\n\n")
        assert _find_listener_pids_for_port(8080) == {123}

    @patch("mcpbridge_wrapper.__main__.os.kill", side_effect=ProcessLookupError())
    def test_pid_exists_false_when_process_missing(self, _mock_kill):
        from mcpbridge_wrapper.__main__ import _pid_exists

        assert _pid_exists(1) is False

    @patch("mcpbridge_wrapper.__main__.os.kill", side_effect=PermissionError())
    def test_pid_exists_true_on_permission_error(self, _mock_kill):
        from mcpbridge_wrapper.__main__ import _pid_exists

        assert _pid_exists(1) is True
