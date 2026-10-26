# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys
import socket
from unittest.mock import patch

import pytest


class TestMainModule:
    """Test suite for main module functionality."""

    def test_main_no_args_starts_interactive_mode_success(self):
        """Test that running 'fab' without arguments automatically enters interactive mode."""
        with patch(
            "fabric_cli.core.fab_interactive.start_interactive_mode"
        ) as mock_start_interactive:
            from fabric_cli.main import main

            with patch.object(sys, "argv", ["fab"]):
                with patch(
                    "fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers"
                ) as mock_get_parsers:
                    mock_parser = type(
                        "MockParser",
                        (),
                        {
                            "parse_args": lambda self: type(
                                "Args", (), {"command": None, "version": False}
                            )(),
                            "set_mode": lambda self, mode: None,
                        },
                    )()
                    mock_subparsers = object()
                    mock_get_parsers.return_value = (mock_parser, mock_subparsers)

                    with patch("fabric_cli.core.fab_state_config.init_defaults"):
                        main()

                    mock_start_interactive.assert_called_once()

    def test_start_interactive_mode_directly_success(self):
        """Test that start_interactive_mode can be called directly without infinite loops."""
        # Mock the InteractiveCLI to prevent actual interactive session
        with patch(
            "fabric_cli.core.fab_interactive.InteractiveCLI"
        ) as mock_interactive_cli:
            from unittest.mock import Mock

            mock_cli_instance = Mock()
            mock_cli_instance._is_running = False
            mock_cli_instance.start_interactive = (
                Mock()
            )  # Mock the start_interactive method
            mock_interactive_cli.return_value = mock_cli_instance

            from fabric_cli.core.fab_interactive import start_interactive_mode

            start_interactive_mode()

            mock_interactive_cli.assert_called_once()
            mock_cli_instance.start_interactive.assert_called_once()

    @pytest.mark.parametrize(
        "tokens",
        [
            ["job", "run", "--help", "--output_format=json"],
            ["--version"],
            ["version"],
        ],
    )
    def test_help_version_no_execution_dependencies_success(
        self,
        tokens: list[str],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from fabric_cli import main as main_module

        monkeypatch.setattr(sys, "argv", ["fab", *tokens])
        with (
            patch("argcomplete.autocomplete") as completion,
            patch("fabric_cli.core.fab_state_config.init_defaults") as init_config,
            patch("fabric_cli.core.fab_logger.print_log_file_path") as log,
            patch.object(main_module, "_execute_command") as execute,
            patch.object(
                socket.socket, "connect", side_effect=AssertionError("network")
            ),
        ):
            if "--help" in tokens:
                with pytest.raises(SystemExit) as exit_info:
                    main_module.main()
                assert exit_info.value.code == 0
            else:
                main_module.main()
            completion.assert_not_called()
            init_config.assert_not_called()
            log.assert_not_called()
            execute.assert_not_called()
        assert capsys.readouterr().err == ""
