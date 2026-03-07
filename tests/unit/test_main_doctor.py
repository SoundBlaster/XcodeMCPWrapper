"""Tests for __main__.py doctor integration."""

from unittest.mock import patch

from mcpbridge_wrapper.__main__ import _parse_doctor_args, main


class TestParseDoctorArgs:
    """Tests for _parse_doctor_args."""

    def test_parse_doctor_flag(self) -> None:
        enabled, remaining = _parse_doctor_args(["--doctor", "--foo"])

        assert enabled is True
        assert remaining == ["--foo"]

    def test_parse_doctor_flag_absent(self) -> None:
        enabled, remaining = _parse_doctor_args(["--foo"])

        assert enabled is False
        assert remaining == ["--foo"]


class TestMainDoctor:
    """Tests for main() behavior in doctor mode."""

    def test_main_doctor_dispatches_to_runner(self) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--doctor", "--web-ui-port", "9191"],
        ), patch("mcpbridge_wrapper.doctor.run_doctor", return_value=1) as run_doctor:
            result = main()

        assert result == 1
        run_doctor.assert_called_once_with(
            web_ui_port=9191,
            web_ui_config=None,
        )

    def test_main_doctor_rejects_broker_flags(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--doctor", "--broker"],
        ):
            result = main()

        assert result == 2
        assert "--doctor cannot be combined with broker mode flags" in capsys.readouterr().err

    def test_main_doctor_rejects_webui_flags(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--doctor", "--web-ui"],
        ):
            result = main()

        assert result == 2
        assert "--doctor cannot be combined with --web-ui flags" in capsys.readouterr().err

    def test_main_doctor_rejects_interactive_modes(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--doctor", "--tui"],
        ):
            result = main()

        assert result == 2
        assert (
            "--doctor cannot be combined with --tui or --broker-console" in capsys.readouterr().err
        )

    def test_main_doctor_rejects_bridge_args(self, capsys) -> None:
        with patch(
            "mcpbridge_wrapper.__main__.sys.argv",
            ["mcpbridge-wrapper", "--doctor", "--", "--foo"],
        ):
            result = main()

        assert result == 2
        assert "--doctor does not accept bridge arguments" in capsys.readouterr().err
