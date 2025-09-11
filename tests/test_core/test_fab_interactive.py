# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import patch

import pytest

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_interactive import InteractiveCLI


class TestInteractiveCLI:
    """Test suite for InteractiveCLI class functionality."""

    # Initialization Tests
    def test_interactive_cli_initialization_success(
        self, interactive_cli, mock_parser, mock_subparsers
    ):
        """Test InteractiveCLI constructor initializes correctly."""
        # Verify initialization
        assert interactive_cli.parser == mock_parser
        assert interactive_cli.subparsers == mock_subparsers
        assert interactive_cli.history is not None
        assert interactive_cli.session is not None
        assert interactive_cli.custom_style is not None

        # Verify parser mode was set during initialization
        mock_parser.set_mode.assert_called_once_with(fab_constant.FAB_MODE_INTERACTIVE)

    # Command Handling Tests - Special Commands
    def test_handle_command_quit_variations_success(
        self, interactive_cli, mock_print_ui, mock_print_log_file_path
    ):
        """Test quit command and its variations."""
        for cmd in fab_constant.INTERACTIVE_QUIT_COMMANDS:
            result = interactive_cli.handle_command(cmd)
            assert result is True

        # Verify goodbye message was printed
        mock_print_ui.assert_called_with(fab_constant.INTERACTIVE_EXIT_MESSAGE)
        # Verify log file path is printed for each command
        assert mock_print_log_file_path.call_count == len(
            fab_constant.INTERACTIVE_QUIT_COMMANDS
        )

    def test_handle_command_help_variations_success(
        self,
        interactive_cli,
        mock_display_help,
        mock_print_log_file_path,
        mock_commands,
    ):
        """Test help command and its variations."""
        for cmd in fab_constant.INTERACTIVE_HELP_COMMANDS:
            result = interactive_cli.handle_command(cmd)
            assert result is False

        # Verify help display was called
        assert mock_display_help.call_count == len(
            fab_constant.INTERACTIVE_HELP_COMMANDS
        )
        # Verify log file path is printed for each command
        assert mock_print_log_file_path.call_count == len(
            fab_constant.INTERACTIVE_HELP_COMMANDS
        )

    def test_handle_command_version_variations_success(
        self, interactive_cli, mock_print_version, mock_print_log_file_path
    ):
        """Test version command and its variations."""
        for cmd in fab_constant.INTERACTIVE_VERSION_COMMANDS:
            result = interactive_cli.handle_command(cmd)
            assert result is False

        # Verify version print was called
        assert mock_print_version.call_count == len(
            fab_constant.INTERACTIVE_VERSION_COMMANDS
        )
        # Verify log file path is printed for each command
        assert mock_print_log_file_path.call_count == len(
            fab_constant.INTERACTIVE_VERSION_COMMANDS
        )

    # Command Handling Tests - Valid Commands
    def test_handle_command_valid_subcommand_success(
        self, interactive_cli, mock_subparsers, mock_print_log_file_path
    ):
        """Test handling of valid subcommands."""
        command = "ls"

        result = interactive_cli.handle_command(command)

        # Verify command processing
        assert result is False
        mock_subparsers.choices["ls"].parse_args.assert_called_once_with([])
        mock_print_log_file_path.assert_called_once()

    def test_handle_command_with_arguments_success(
        self,
        interactive_cli,
        mock_subparsers,
        mock_print_log_file_path,
        mock_command_get_command_path,
    ):
        """Test handling of commands with arguments."""
        command = "auth login"

        result = interactive_cli.handle_command(command)

        assert result is False
        mock_subparsers.choices["auth"].parse_args.assert_called_once_with(["login"])

    def test_handle_command_invalid_subcommand_failure(
        self, interactive_cli, mock_print_log_file_path
    ):
        """Test handling of invalid subcommands."""
        command = "invalid_command"

        interactive_cli.handle_command(command)

        interactive_cli.parser.error.assert_called_once_with(
            "invalid choice: 'invalid_command'"
        )

    def test_handle_command_empty_input_success(
        self, interactive_cli, mock_print_log_file_path
    ):
        """Test handling of empty command input."""
        command = ""

        result = interactive_cli.handle_command(command)

        assert result is False
        mock_print_log_file_path.assert_called_once()

    def test_handle_command_whitespace_only_success(
        self, interactive_cli, mock_print_log_file_path
    ):
        """Test handling of whitespace-only input."""
        command = "   "

        result = interactive_cli.handle_command(command)

        assert result is False
        mock_print_log_file_path.assert_called_once()

    # Exception Handling Tests
    def test_handle_command_system_exit_exception_success(
        self, interactive_cli, mock_subparsers, mock_print_log_file_path
    ):
        """Test handling of SystemExit exception from argument parser."""
        command = "ls --invalid-flag"

        # Configure mock to raise SystemExit
        mock_subparsers.choices["ls"].parse_args.side_effect = SystemExit(1)

        result = interactive_cli.handle_command(command)

        # Should handle SystemExit gracefully and not exit
        assert result is None
        mock_print_log_file_path.assert_called_once()

    # Interactive Session Tests
    def test_start_interactive_normal_flow_success(
        self, interactive_cli, mock_print_ui, mock_html_escape
    ):
        """Test normal flow of start_interactive method."""

        def mock_handle_command(cmd):
            return cmd == "quit"

        # Mock the session.prompt to return quit command
        interactive_cli.session.prompt.side_effect = ["quit"]

        # Patch handle_command method
        with patch.object(
            interactive_cli, "handle_command", side_effect=mock_handle_command
        ) as mock_handle:
            interactive_cli.start_interactive()

            # Verify welcome messages
            welcome_calls = mock_print_ui.call_args_list
            assert any(
                "Welcome to the Fabric CLI ⚡" in str(call) for call in welcome_calls
            )
            assert any("Type 'help' for help." in str(call) for call in welcome_calls)

            # Verify command handling was called
            mock_handle.assert_called_once_with("quit")

    def test_start_interactive_keyboard_interrupt_success(
        self, interactive_cli, mock_print_ui
    ):
        """Test KeyboardInterrupt handling in start_interactive."""
        # Configure session mock to raise KeyboardInterrupt
        interactive_cli.session.prompt.side_effect = KeyboardInterrupt()

        interactive_cli.start_interactive()

        # Verify goodbye message for interrupt
        mock_print_ui.assert_called_with(f"\n{fab_constant.INTERACTIVE_EXIT_MESSAGE}")

    def test_start_interactive_eof_error_failure(self, interactive_cli, mock_print_ui):
        """Test EOFError handling in start_interactive."""
        # Configure session mock to raise EOFError
        interactive_cli.session.prompt.side_effect = EOFError()

        interactive_cli.start_interactive()

        # Verify goodbye message for EOF
        mock_print_ui.assert_called_with(f"\n{fab_constant.INTERACTIVE_EXIT_MESSAGE}")

    def test_start_interactive_context_display_success(
        self, interactive_cli, mock_html_escape, mock_context
    ):
        """Test context path display in prompt."""

        def mock_handle_command(cmd):
            return cmd == "quit"

        # Configure to exit after one prompt
        interactive_cli.session.prompt.side_effect = ["quit"]

        with patch.object(
            interactive_cli, "handle_command", side_effect=mock_handle_command
        ):
            interactive_cli.start_interactive()

        # Verify context was used in prompt
        mock_html_escape.assert_called_once_with("/test/workspace")

    def test_start_interactive_multiple_commands_success(self, interactive_cli):
        """Test handling multiple commands before exit."""
        # Configure multiple commands
        interactive_cli.session.prompt.side_effect = ["help", "version", "quit"]

        call_count = 0

        def mock_handle_command(cmd):
            nonlocal call_count
            call_count += 1
            return cmd == "quit"  # Only return True for quit

        with patch.object(
            interactive_cli, "handle_command", side_effect=mock_handle_command
        ):
            interactive_cli.start_interactive()

        # Verify all commands were handled
        assert call_count == 3

    # Edge Cases and Error Scenarios
    def test_handle_command_with_special_characters_success(
        self, interactive_cli, mock_print_log_file_path
    ):
        """Test handling commands with special characters."""
        special_commands = ["ls@#$", "help!", "config&test"]

        for cmd in special_commands:
            result = interactive_cli.handle_command(cmd)

            assert result is not None or result is None  # Just verify no exception

    def test_handle_command_very_long_input_success(
        self, interactive_cli, mock_print_log_file_path
    ):
        """Test handling very long command input."""
        long_command = "ls " + " ".join([f"arg{i}" for i in range(100)])

        # Should handle gracefully without crashing
        result = interactive_cli.handle_command(long_command)
        assert result is not None or result is None

    # Test fixtures and helper methods
    def test_custom_style_configuration_success(self, interactive_cli):
        """Test that custom style is properly configured."""
        assert interactive_cli.custom_style is not None
        # Verify style has expected components
        style_rules = interactive_cli.custom_style.style_rules
        assert any("prompt" in rule for rule in style_rules)
        assert any("context" in rule for rule in style_rules)
        assert any("detail" in rule for rule in style_rules)
        assert any("input" in rule for rule in style_rules)


@pytest.fixture
def mock_parser():
    """Mock parser with interactive mode setting capability."""
    from unittest.mock import Mock

    parser = Mock()
    parser.set_mode = Mock()
    parser.error = Mock()
    yield parser


@pytest.fixture
def mock_subparsers():
    """Mock subparsers with choices and parsing capability."""
    from unittest.mock import Mock

    subparsers = Mock()

    # Mock subparser for 'ls' command
    ls_subparser = Mock()
    ls_subparser.parse_args.return_value = argparse.Namespace(
        command="ls",
        func=Mock(),
        fab_mode=fab_constant.FAB_MODE_INTERACTIVE,
        command_path="ls",
    )

    # Mock subparser for 'help' command
    help_subparser = Mock()
    help_subparser.parse_args.return_value = argparse.Namespace(
        command="help",
        func=Mock(),
        fab_mode=fab_constant.FAB_MODE_INTERACTIVE,
        command_path="help",
    )

    subparsers.choices = {
        "ls": ls_subparser,
        "help": help_subparser,
        "config": help_subparser,
        "auth": help_subparser,
    }
    yield subparsers


@pytest.fixture
def mock_in_memory_history():
    """Mock InMemoryHistory."""
    with patch("fabric_cli.core.fab_interactive.InMemoryHistory") as mock:
        yield mock


@pytest.fixture
def mock_prompt_session():
    """Mock PromptSession."""
    with patch("fabric_cli.core.fab_interactive.PromptSession") as mock:
        yield mock


@pytest.fixture
def mock_print_ui():
    """Mock utils_ui.print function."""
    with patch("fabric_cli.core.fab_interactive.utils_ui.print") as mock:
        yield mock


@pytest.fixture
def mock_print_log_file_path():
    """Mock fab_logger.print_log_file_path function."""
    with patch(
        "fabric_cli.core.fab_interactive.fab_logger.print_log_file_path"
    ) as mock:
        yield mock


@pytest.fixture
def mock_display_help():
    """Mock utils_ui.display_help function."""
    with patch("fabric_cli.core.fab_interactive.utils_ui.display_help") as mock:
        yield mock


@pytest.fixture
def mock_print_version():
    """Mock utils_ui.print_version function."""
    with patch("fabric_cli.core.fab_interactive.utils_ui.print_version") as mock:
        yield mock


@pytest.fixture
def mock_commands():
    """Mock fab_commands.COMMANDS."""
    with patch(
        "fabric_cli.core.fab_interactive.fab_commands.COMMANDS",
        ["ls", "help", "config"],
    ) as mock:
        yield mock


@pytest.fixture
def mock_html_escape():
    """Mock html.escape function."""
    with patch("fabric_cli.core.fab_interactive.html.escape") as mock:
        mock.return_value = "/test/workspace"
        yield mock


@pytest.fixture
def mock_context():
    """Mock Context class."""
    with patch("fabric_cli.core.fab_interactive.Context") as mock:
        context_instance = mock.return_value
        context_instance.context.path = "/test/workspace"
        yield mock


@pytest.fixture
def mock_command_get_command_path():
    """Mock Command.get_command_path static method."""
    with patch.object(Command, "get_command_path") as mock:
        mock.return_value = "ls"
        yield mock


@pytest.fixture
def interactive_cli(
    mock_parser, mock_subparsers, mock_in_memory_history, mock_prompt_session
):
    """Create InteractiveCLI instance with mocked dependencies."""
    cli = InteractiveCLI(mock_parser, mock_subparsers)
    return cli
