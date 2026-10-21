# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys
from argparse import Namespace
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_decorators import handle_exceptions
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_parser_setup import create_parser_and_subparsers


class TestMainModule:
    """Test suite for main module functionality."""

    @pytest.mark.parametrize("command", ["ls", "pwd"])
    def test_command_string_reports_unflagged_command_error(self, command: str) -> None:
        """Child-parser dispatch reports the original error and failure code."""
        from fabric_cli.main import main

        parser, subparsers = create_parser_and_subparsers()
        error = FabricCLIError("Command failed", fab_constant.ERROR_INVALID_INPUT)

        @handle_exceptions()
        def fail(args: Namespace) -> None:
            raise error

        subparsers.choices[command].set_defaults(func=fail)
        with (
            patch(
                "fabric_cli.main.get_global_parser_and_subparsers",
                return_value=(parser, subparsers),
            ),
            patch("fabric_cli.main.argcomplete.autocomplete"),
            patch("fabric_cli.main.fab_state_config.init_defaults"),
            patch("fabric_cli.main.fab_logger.print_log_file_path"),
            patch("fabric_cli.utils.fab_ui.print_output_error") as print_error,
            patch.object(sys, "argv", ["fab", "-c", command]),
        ):
            with pytest.raises(SystemExit) as exc:
                main()

        assert exc.value.code == fab_constant.EXIT_CODE_ERROR
        print_error.assert_called_once_with(error, command, output_format_type=None)

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
                            "parse_args": lambda: type(
                                "Args", (), {"command": None, "version": False}
                            )(),
                            "set_mode": lambda mode: None,
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
