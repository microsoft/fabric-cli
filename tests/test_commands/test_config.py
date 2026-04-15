# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

import pytest

import fabric_cli.core.fab_constant as constant
from fabric_cli.core.fab_context import Context
from fabric_cli.errors import ErrorMessages
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.data.static_test_data import StaticTestData


class TestConfig:
    # region config SET
    def test_config_set_success(self, mock_print_done, cli_executor: CLIExecutor):
        # Execute command
        cli_executor.exec_command(f"config set debug_enabled true")

        # Extract the arguments passed to the mock
        call_args, _ = mock_print_done.call_args

        # Assert
        mock_print_done.assert_called_once()
        assert "debug_enabled" in call_args[0].lower()
        assert "true" in call_args[0]

    def test_config_set_default_capacity_success(
        self, mock_print_done, cli_executor: CLIExecutor, test_data: StaticTestData
    ):
        # Execute command
        cli_executor.exec_command(
            f"config set {constant.FAB_DEFAULT_CAPACITY} {test_data.capacity.name}"
        )

        # Extract the arguments passed to the mock
        call_args, _ = mock_print_done.call_args

        # Assert
        mock_print_done.assert_called_once()
        assert constant.FAB_DEFAULT_CAPACITY in call_args[0].lower()
        assert test_data.capacity.name in call_args[0]

    def test_config_set_default_capacity_invalid_capacity_failure(
        self,
        mock_print_done,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        capacity_name = test_data.capacity.name + "?"
        expected_message = ErrorMessages.Config.invalid_capacity(capacity_name)

        # Execute command
        cli_executor.exec_command(
            f"config set {constant.FAB_DEFAULT_CAPACITY} {capacity_name}"
        )

        # Assert
        mock_print_done.assert_not_called()
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT, expected_message)

    def test_config_set_unknown_key_failure(
        self, mock_print_done, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Setup
        key = constant.FAB_MODE + "?"
        expected_message = ErrorMessages.Config.unknown_configuration_key(key)

        # Execute command
        cli_executor.exec_command(f"config set {key} {constant.FAB_MODE_INTERACTIVE}")

        # Assert
        mock_print_done.assert_not_called()
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT, expected_message)

    def test_config_set_invalid_value_failure(
        self, mock_print_done, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Execute command - invalid value for a real config key
        cli_executor.exec_command(f"config set {constant.FAB_CACHE_ENABLED} invalid")

        # Assert
        mock_print_done.assert_not_called()
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_config_set_invalid_path_failure(
        self, mock_print_done, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Setup
        invalidPath = "Invalid_path"
        expected_message = ErrorMessages.Common.file_or_directory_not_exists()

        # Execute command
        cli_executor.exec_command(
            f"config set {constant.FAB_LOCAL_DEFINITION_LABELS} {invalidPath}"
        )

        # Assert
        mock_print_done.assert_not_called()
        assert_fabric_cli_error(constant.ERROR_INVALID_PATH, expected_message)

    # endregion

    # region config GET
    def test_config_get_success(
        self, mock_questionary_print, cli_executor: CLIExecutor
    ):
        # Setup
        value = "myresourcegroup"
        cli_executor.exec_command(
            f"config set {constant.FAB_DEFAULT_AZ_RESOURCE_GROUP} {value}"
        )

        # Execute command
        cli_executor.exec_command(
            f"config get {constant.FAB_DEFAULT_AZ_RESOURCE_GROUP}"
        )

        # Extract the arguments passed to the mock
        call_args, _ = mock_questionary_print.call_args

        # Assert
        # question.print is called twice. once in the setup in config_set and once in config_get
        mock_questionary_print.assert_called()
        assert any(value in call.args[0] for call in mock_questionary_print.mock_calls)

    def test_config_get_unknown_key_failure(
        self,
        mock_questionary_print,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        key = constant.FAB_DEFAULT_AZ_RESOURCE_GROUP + "?"
        expected_message = ErrorMessages.Config.unknown_configuration_key(key)

        # Execute command
        cli_executor.exec_command(f"config get {key}")

        # Assert
        mock_questionary_print.assert_not_called()
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT, expected_message)

    # endregion

    # region config LS
    def test_config_ls_success(self, mock_questionary_print, cli_executor: CLIExecutor):
        # Execute command
        cli_executor.exec_command("config ls")

        # Assert
        for key in constant.FAB_CONFIG_KEYS_TO_VALID_VALUES:
            assert any(
                key in call.args[0] for call in mock_questionary_print.mock_calls
            )

    # endregion

    # region config CLEAR-CACHE
    def test_config_clear_cache_success(
        self, mock_print_done, cli_executor: CLIExecutor
    ):
        # Execute command
        with patch("fabric_cli.utils.fab_mem_store.clear_caches") as mock_clear_caches:
            cli_executor.exec_command("config clear-cache")

            # Assert
            mock_clear_caches.assert_called_once()
            mock_print_done.assert_called_once()

    # endregion


DEPRECATION_PREFIX = "The 'mode' setting is deprecated. "
DEPRECATION_COMMANDLINE_SUFFIX = (
    "Run 'fab' without arguments to enter REPL mode, "
    "or use 'fab <command>' for command-line mode."
)
DEPRECATION_INTERACTIVE_SUFFIX = (
    "Run 'exit' to leave the REPL, then use 'fab <command>' for command-line mode."
)
DEPRECATION_WARNING_COMMANDLINE = DEPRECATION_PREFIX + DEPRECATION_COMMANDLINE_SUFFIX
DEPRECATION_WARNING_INTERACTIVE = DEPRECATION_PREFIX + DEPRECATION_INTERACTIVE_SUFFIX


class TestConfigModeDeprecated:
    """Unit tests for mode deprecation in config set/get commands."""

    @pytest.fixture(autouse=True)
    def _reset_runtime_mode(self):
        """Ensure runtime mode is always restored to interactive after each test."""
        yield
        Context().set_runtime_mode(constant.FAB_MODE_INTERACTIVE)

    @pytest.fixture
    def mock_repl(self):
        with patch("fabric_cli.core.fab_interactive.start_interactive_mode") as mock:
            yield mock

    def test_config_set_mode_interactive_warns_and_launches_repl_success(
        self, mock_print_warning, mock_repl, cli_executor: CLIExecutor
    ):
        """'config set mode interactive' must warn and launch REPL."""
        cli_executor.exec_command(f"config set mode {constant.FAB_MODE_INTERACTIVE}")

        mock_print_warning.assert_called_once_with(DEPRECATION_WARNING_INTERACTIVE)
        mock_repl.assert_called_once()

    @pytest.mark.parametrize("mode_value", [
        constant.FAB_MODE_COMMANDLINE,
        "bogus_value",
    ])
    def test_config_set_mode_non_interactive_warns_without_repl_success(
        self, mode_value, mock_print_warning, mock_repl, cli_executor: CLIExecutor
    ):
        """'config set mode command_line' (or bogus) must warn but not launch REPL."""
        cli_executor.exec_command(f"config set mode {mode_value}")

        mock_print_warning.assert_called_once_with(DEPRECATION_WARNING_INTERACTIVE)
        mock_repl.assert_not_called()

    def test_config_set_mode_in_commandline_warns_with_fab_hint_success(
        self, mock_print_warning, mock_repl, cli_executor: CLIExecutor
    ):
        """'config set mode command_line' in command-line mode must show fab hint."""
        Context().set_runtime_mode(constant.FAB_MODE_COMMANDLINE)
        cli_executor.exec_command(f"config set mode {constant.FAB_MODE_COMMANDLINE}")

        mock_print_warning.assert_called_once_with(DEPRECATION_WARNING_COMMANDLINE)
        mock_repl.assert_not_called()

    def test_config_set_non_mode_key_still_works_success(
        self, mock_print_done, cli_executor: CLIExecutor
    ):
        """Other config keys should still be writable."""
        cli_executor.exec_command(f"config set {constant.FAB_DEBUG_ENABLED} true")
        mock_print_done.assert_called_once()

    def test_config_get_mode_warns_and_returns_runtime_mode_success(
        self, mock_questionary_print, mock_print_warning, cli_executor: CLIExecutor
    ):
        """'config get mode' must warn and return the runtime mode."""
        cli_executor.exec_command("config get mode")

        mock_print_warning.assert_any_call(DEPRECATION_WARNING_INTERACTIVE)
        mock_questionary_print.assert_called()

    def test_config_get_mode_in_commandline_warns_with_fab_hint_success(
        self, mock_questionary_print, mock_print_warning, cli_executor: CLIExecutor
    ):
        """'config get mode' in command-line mode must show fab hint."""
        Context().set_runtime_mode(constant.FAB_MODE_COMMANDLINE)
        cli_executor.exec_command("config get mode")

        mock_print_warning.assert_any_call(DEPRECATION_WARNING_COMMANDLINE)
        mock_questionary_print.assert_called()

    def test_config_get_non_mode_key_still_works_success(
        self, mock_questionary_print, cli_executor: CLIExecutor
    ):
        """Other config keys should still be readable."""
        cli_executor.exec_command(f"config get {constant.FAB_DEBUG_ENABLED}")
        mock_questionary_print.assert_called()
