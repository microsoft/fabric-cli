# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import time
from unittest.mock import patch

import fabric_cli.commands.fs.fab_fs_get as fab_get
import fabric_cli.commands.fs.fab_fs_start as fab_start
import fabric_cli.commands.fs.fab_fs_stop as fab_stop
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType


class TestStart:
    # region Capacity
    def test_start_capacity_success(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        setup_config_values_for_capacity,
        mock_print_done,
        mock_questionary_print,
        mock_questionary_confirm,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)
        stop(capacity.full_path)
        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"start {capacity.full_path} --force")

        # Assert
        mock_print_done.assert_called_once()
        assert capacity.display_name in mock_print_done.call_args[0][0]

        mock_questionary_confirm.assert_not_called()  # force is enabled

        mock_questionary_print.reset_mock()
        get(capacity.full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert '"state": "Active"' in mock_questionary_print.call_args[0][0]

    def test_start_capacity_without_force_success(
        self,
        virtual_workspace_item_factory,
        setup_config_values_for_capacity,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        mock_print_warning,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)
        stop(capacity.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(f"start {capacity.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert capacity.display_name in mock_print_done.call_args[0][0]

        mock_confirm.assert_called()  # force is disabled

        mock_questionary_print.reset_mock()
        get(capacity.full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert '"state": "Active"' in mock_questionary_print.call_args[0][0]

    def test_start_capacity_without_force_cancel_operation_success(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        setup_config_values_for_capacity,
        mock_print_done,
        mock_questionary_print,
        mock_print_warning,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)
        stop(capacity.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            # Simulate user cancel the operation
            mock_confirm.return_value.ask.return_value = False

            # Execute command
            cli_executor.exec_command(f"start {capacity.full_path}")

        # Assert
        mock_print_warning.assert_called_once()
        mock_print_done.assert_not_called()
        mock_questionary_print.assert_not_called()
        mock_confirm.assert_called()  # force is disabled

        # Reset mock
        mock_print_warning.reset_mock()
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        # Assert - check capacity is still stopped
        get(capacity.full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert '"state": "Paused"' in mock_questionary_print.call_args[0][0]

    def test_start_capacity_already_active_failure(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        setup_config_values_for_capacity,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)

        # Execute command

        cli_executor.exec_command(f"start {capacity.full_path} --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_RUNNING)

    # endregion

    # region Mirrored DB
    def test_start_mirrored_db_success(
        self,
        item_factory,
        cli_executor,
        mock_print_done,
        mock_questionary_confirm,
        mock_questionary_print,
    ):
        # Setup
        mirrored_db = item_factory(ItemType.MIRRORED_DATABASE)
        mock_print_done.reset_mock()

        # TODO: delete this line after mirrored db fix the API GAP for Create
        time.sleep(60)

        # Execute command
        cli_executor.exec_command(f"start {mirrored_db.full_path} --force")

        # Assert
        mock_print_done.assert_called_once()
        assert mirrored_db.display_name in mock_print_done.call_args[0][0]

        mock_questionary_confirm.assert_not_called()

        mock_questionary_print.reset_mock()
        # The status is Initializing, so we need to wait until it is Running
        time.sleep(30)
        get(mirrored_db.full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert '"status": "Running"' in mock_questionary_print.call_args[0][0]

    def test_start_mirrored_db_already_active_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        mirrored_db = item_factory(ItemType.MIRRORED_DATABASE)
        # TODO: delete this line after mirrored db fix the API GAP for Create
        time.sleep(30)
        start(mirrored_db.full_path)

        # The status is Initializing, so we need to wait until it is Running
        time.sleep(30)

        # Execute command
        cli_executor.exec_command(f"start {mirrored_db.full_path} --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_RUNNING)

    # endregion


# region Helper Methods
def stop(path, force=True):
    args = _build_stop_args(path, force)
    context = handle_context.get_command_context(args.path)
    fab_stop.exec_command(args, context)


def _build_stop_args(path, force):
    return argparse.Namespace(
        command="stop", command_path="stop", path=path, force=force
    )


def start(path, force=True):
    args = _build_start_args(path, force)
    context = handle_context.get_command_context(args.path)
    fab_start.exec_command(args, context)


def _build_start_args(path, force):
    return argparse.Namespace(
        command="start", command_path="start", path=path, force=force
    )


def get(path, output=None, query=None, deep_traversal=False):
    args = _build_get_args(path, output, query, deep_traversal)
    context = handle_context.get_command_context(args.path)
    fab_get.exec_command(args, context)


def _build_get_args(path, output=None, query=None, deep_traversal=False):
    return argparse.Namespace(
        command="get",
        acl_subcommand="get",
        command_path="get",
        path=path,
        output=output,
        query=[query] if query else None,
        deep_traversal=deep_traversal,
        force=True,
    )


# endregion
