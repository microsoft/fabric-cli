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

    def test_handle_command_fab_in_interactive_mode_success(
        self, interactive_cli, mock_print_ui, mock_print_log_file_path
    ):
        """Test that typing 'fab' in interactive mode shows appropriate message."""
        result = interactive_cli.handle_command("fab")

        # Verify it stays in interactive mode and shows message
        assert result is False
        mock_print_ui.assert_called_with("In interactive mode, commands don't require the fab prefix. Use --help to view the list of supported commands.")
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
            "invalid choice: 'invalid_command'. Type 'help' for available commands."
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
        # Configure session mock to raise KeyboardInterrupt once, then quit
        interactive_cli.session.prompt.side_effect = [KeyboardInterrupt(), "quit"]

        # Mock handle_command to return True for quit
        def mock_handle_command(cmd):
            return cmd == "quit"

        with patch.object(
            interactive_cli, "handle_command", side_effect=mock_handle_command
        ):
            interactive_cli.start_interactive()

        # Verify that Ctrl+C message is shown and then exit message
        calls = mock_print_ui.call_args_list
        ctrl_c_message_found = any(
            "Use 'quit' or 'exit' to leave interactive mode." in str(call)
            for call in calls
        )
        assert ctrl_c_message_found, "Should show Ctrl+C handling message"

    def test_start_interactive_eof_error_failure(self, interactive_cli, mock_print_ui):
        """Test EOFError handling in start_interactive."""
        # Configure session mock to raise EOFError once, then quit
        interactive_cli.session.prompt.side_effect = [EOFError(), "quit"]

        # Mock handle_command to return True for quit
        def mock_handle_command(cmd):
            return cmd == "quit"

        with patch.object(
            interactive_cli, "handle_command", side_effect=mock_handle_command
        ):
            interactive_cli.start_interactive()

        # Verify that EOF error message is shown
        calls = mock_print_ui.call_args_list
        error_message_found = any(
            "Error in interactive session:" in str(call) or "Session will continue" in str(call)
            for call in calls
        )
        assert error_message_found, "Should show EOF error handling message"

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

    # Test fab + enter automatic mode switching
    def test_main_no_args_starts_interactive_mode_success(self):
        """Test that running 'fab' without arguments automatically enters interactive mode."""
        with patch("fabric_cli.main._start_auto_repl") as mock_start_auto_repl:
            import sys

            from fabric_cli.main import main

            with patch.object(sys, 'argv', ['fab']):
                with patch("fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers") as mock_get_parsers:
                    mock_parser = type('MockParser', (), {
                        'parse_args': lambda: type('Args', (), {
                            'command': None,
                            'version': False
                        })(),
                        'set_mode': lambda mode: None
                    })()
                    mock_subparsers = object()
                    mock_get_parsers.return_value = (mock_parser, mock_subparsers)
                    
                    with patch("fabric_cli.core.fab_state_config.init_defaults"):
                        main()
                    
                    mock_start_auto_repl.assert_called_once()

    def test_start_auto_repl_calls_interactive_mode_success(self):
        """Test that _start_auto_repl properly calls start_interactive_mode."""
        with patch("fabric_cli.core.fab_interactive.start_interactive_mode") as mock_start_interactive:
            from fabric_cli.main import _start_auto_repl
            
            _start_auto_repl()
            
            mock_start_interactive.assert_called_once()

    def test_start_auto_repl_handles_exceptions_success(self):
        """Test that _start_auto_repl handles exceptions gracefully."""
        with patch("fabric_cli.core.fab_interactive.start_interactive_mode") as mock_start_interactive, \
             patch("fabric_cli.utils.fab_ui.print_output_error") as mock_print_error, \
             patch("sys.exit") as mock_exit:
            
            mock_start_interactive.side_effect = Exception("Test error")
            
            from fabric_cli.main import _start_auto_repl
            _start_auto_repl()
            
            mock_start_interactive.assert_called_once()
            mock_print_error.assert_called_once()
            mock_exit.assert_called_once()

    def test_fab_command_in_interactive_mode_shows_message_success(
        self, interactive_cli, mock_print_ui, mock_print_log_file_path
    ):
        """Test that running 'fab' while already in interactive mode shows informative message."""
        result = interactive_cli.handle_command("fab")

        # Verify it stays in interactive mode and shows message
        assert result is False
        mock_print_ui.assert_called_with("In interactive mode, commands don't require the fab prefix. Use --help to view the list of supported commands.")
        mock_print_log_file_path.assert_called_once()

    def test_interactive_cli_singleton_pattern_success(self):
        """Test that InteractiveCLI follows singleton pattern"""
        from fabric_cli.core.fab_interactive import InteractiveCLI
    
        with patch("fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers") as mock_get_parsers:
            mock_parser = type('MockParser', (), {'set_mode': lambda self, mode: None})()
            mock_subparsers = object()
            mock_get_parsers.return_value = (mock_parser, mock_subparsers)
            
            # Create two instances
            instance1 = InteractiveCLI()
            instance2 = InteractiveCLI()
            
            # Should be the same instance
            assert instance1 is instance2

    def test_start_interactive_mode_success(self):
        """Test mode switching creates singleton and launches interactive CLI"""
        with patch("fabric_cli.core.fab_interactive.InteractiveCLI") as mock_interactive_cli:
            from unittest.mock import Mock
            
            mock_cli_instance = Mock()
            mock_cli_instance._is_running = False
            mock_interactive_cli.return_value = mock_cli_instance
            
            from fabric_cli.core.fab_interactive import start_interactive_mode
            start_interactive_mode()
            
            mock_interactive_cli.assert_called_once()
            mock_cli_instance.start_interactive.assert_called_once()

    def test_start_interactive_mode_already_running(self):
        """Test that calling start_interactive_mode when already running prints message"""
        with patch("fabric_cli.core.fab_interactive.InteractiveCLI") as mock_interactive_cli, \
             patch("fabric_cli.core.fab_interactive.utils_ui.print") as mock_print:
            from unittest.mock import Mock
            from fabric_cli.core import fab_interactive
            
            mock_cli_instance = Mock()
            mock_cli_instance._is_running = True
            mock_interactive_cli.return_value = mock_cli_instance
            
            # Mock the start_interactive method to simulate the actual behavior
            def mock_start_interactive():
                if mock_cli_instance._is_running:
                    mock_print("Interactive mode is already running.")
                    return
            
            mock_cli_instance.start_interactive = mock_start_interactive
            
            fab_interactive.start_interactive_mode()
            
            # Should call InteractiveCLI() and then start_interactive should print message
            mock_interactive_cli.assert_called_once()
            mock_print.assert_called_once_with("Interactive mode is already running.")


    # endregion

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
    from fabric_cli.core.fab_interactive import InteractiveCLI
    
    # Mock the get_global_parser_and_subparsers function to return our mocks
    with patch("fabric_cli.core.fab_parser_setup.get_global_parser_and_subparsers") as mock_get_parsers:
        mock_get_parsers.return_value = (mock_parser, mock_subparsers)
        
        # Create a fresh InteractiveCLI instance for each test by directly creating an instance
        # and assigning the mock objects to ensure tests use the same mocks
        cli = InteractiveCLI(mock_parser, mock_subparsers)
        
        # Ensure the instance uses our mock objects
        cli.parser = mock_parser
        cli.subparsers = mock_subparsers
        
        yield cli
