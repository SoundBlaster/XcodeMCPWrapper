"""Tests for __main__.py terminal frontend integration."""

import json
from unittest.mock import patch

from mcpbridge_wrapper.__main__ import _parse_broker_console_args, _parse_tui_args, main


class TestParseTUIArgs:
    """Tests for _parse_tui_args."""

    def test_parse_tui_flag(self) -> None:
        enabled, remaining = _parse_tui_args(["--tui", "--foo"])

        assert enabled is True
        assert remaining == ["--foo"]

    def test_parse_tui_flag_absent(self) -> None:
        enabled, remaining = _parse_tui_args(["--foo"])

        assert enabled is False
        assert remaining == ["--foo"]


class TestParseBrokerConsoleArgs:
    """Tests for _parse_broker_console_args."""

    def test_parse_broker_console_flag(self) -> None:
        enabled, remaining = _parse_broker_console_args(["--broker-console", "--foo"])

        assert enabled is True
        assert remaining == ["--foo"]

    def test_parse_broker_console_flag_absent(self) -> None:
        enabled, remaining = _parse_broker_console_args(["--foo"])

        assert enabled is False
        assert remaining == ["--foo"]


class TestMainTUI:
    """Tests for main() behavior in standalone terminal frontend mode."""

    def test_main_tui_runs_terminal_frontend(self, tmp_path) -> None:
        config_path = tmp_path / "webui.json"
        config_path.write_text(
            json.dumps(
                {
                    "host": "127.0.0.1",
                    "port": 9091,
                    "auth": {
                        "enabled": True,
                        "username": "alice",
                        "password": "secret",
                    },
                }
            )
        )

        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--tui", "--web-ui-config", str(config_path)],
        ), patch("mcpbridge_wrapper.__main__.sys.stdin") as mock_stdin, patch(
            "mcpbridge_wrapper.__main__.sys.stdout"
        ) as mock_stdout, patch("mcpbridge_wrapper.tui.run_tui", return_value=0) as run_tui:
            mock_stdin.isatty.return_value = True
            mock_stdout.isatty.return_value = True

            result = main()

        assert result == 0
        runtime = run_tui.call_args.args[0]
        assert runtime.base_url == "http://127.0.0.1:9091"
        assert runtime.auth_header is not None
        assert runtime.auth_header.startswith("Basic ")

    def test_main_tui_rejects_broker_flags(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--tui", "--broker"],
        ):
            result = main()

        assert result == 2
        assert "--tui cannot be combined with broker mode flags" in capsys.readouterr().err

    def test_main_tui_rejects_webui_flags(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--tui", "--web-ui"],
        ):
            result = main()

        assert result == 2
        assert "--tui cannot be combined with --web-ui flags" in capsys.readouterr().err

    def test_main_tui_rejects_bridge_args(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--tui", "--", "--foo"],
        ):
            result = main()

        assert result == 2
        assert "--tui does not accept bridge arguments" in capsys.readouterr().err

    def test_main_tui_requires_interactive_terminal(self, capsys) -> None:
        with patch("mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper", "--tui"]), patch(
            "mcpbridge_wrapper.__main__.sys.stdin"
        ) as mock_stdin, patch("mcpbridge_wrapper.__main__.sys.stdout") as mock_stdout:
            mock_stdin.isatty.return_value = False
            mock_stdout.isatty.return_value = True

            result = main()

        assert result == 2
        assert "--tui requires an interactive terminal" in capsys.readouterr().err


class TestMainBrokerConsole:
    """Tests for main() behavior in one-command broker console mode."""

    def test_main_broker_console_dispatches_to_orchestrator(self) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-console", "--web-ui-port", "9191"],
        ), patch("mcpbridge_wrapper.__main__.sys.stdin") as mock_stdin, patch(
            "mcpbridge_wrapper.__main__.sys.stdout"
        ) as mock_stdout, patch(
            "mcpbridge_wrapper.__main__._run_broker_console", return_value=0
        ) as run_console:
            mock_stdin.isatty.return_value = True
            mock_stdout.isatty.return_value = True

            result = main()

        assert result == 0
        run_console.assert_called_once_with(
            web_ui_port=9191,
            web_ui_config=None,
            web_ui_restart=False,
        )

    def test_main_broker_console_requires_interactive_terminal(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv", ["mcpbridge-wrapper", "--broker-console"]
        ), patch("mcpbridge_wrapper.__main__.sys.stdin") as mock_stdin, patch(
            "mcpbridge_wrapper.__main__.sys.stdout"
        ) as mock_stdout:
            mock_stdin.isatty.return_value = False
            mock_stdout.isatty.return_value = True

            result = main()

        assert result == 2
        assert "--broker-console requires an interactive terminal" in capsys.readouterr().err

    def test_main_broker_console_rejects_broker_flags(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-console", "--broker"],
        ):
            result = main()

        assert result == 2
        assert (
            "--broker-console cannot be combined with broker mode flags" in capsys.readouterr().err
        )

    def test_main_broker_console_rejects_bridge_args(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--broker-console", "--", "--foo"],
        ):
            result = main()

        assert result == 2
        assert "--broker-console does not accept bridge arguments" in capsys.readouterr().err

    def test_main_rejects_tui_with_broker_console(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--tui", "--broker-console"],
        ):
            result = main()

        assert result == 2
        assert "--tui cannot be combined with --broker-console" in capsys.readouterr().err
