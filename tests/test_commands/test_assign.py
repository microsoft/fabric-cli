# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import patch

import fabric_cli.commands.fs.fab_fs_unassign as fab_unassign
from fabric_cli.commands.fs import fab_fs_get
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType
from tests.test_commands.data.static_test_data import StaticTestData


class TestAssign:
    # region ASSIGN
    def test_assign_capacity_workspace_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_without_capacity = workspace_factory()
        unassign(
            f"/.capacities/{test_data.capacity.name}.Capacity",
            workspace_without_capacity.full_path,
        )

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        cli_executor.exec_command(
            f"assign {capacity_full_path} --workspace {workspace_without_capacity.full_path} --force"
        )

        # Assert
        get(workspace_without_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_assign_capacity_workspace_without_force_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_without_capacity = workspace_factory()
        unassign(
            f"/.capacities/{test_data.capacity.name}.Capacity",
            workspace_without_capacity.full_path,
        )

        # Reset mock
        mock_questionary_print.reset_mock()

        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            # Execute command
            cli_executor.exec_command(
                f"assign {capacity_full_path} --workspace {workspace_without_capacity.full_path}"
            )

        # Assert
        mock_confirm.assert_called()  # force is disabled
        get(workspace_without_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_assign_capacity_workspace_without_force_cancel_operation_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_without_capacity = workspace_factory()
        unassign(
            f"/.capacities/{test_data.capacity.name}.Capacity",
            workspace_without_capacity.full_path,
        )

        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            # Execute command
            cli_executor.exec_command(
                f"assign {capacity_full_path} --workspace {workspace_without_capacity.full_path}"
            )

        # Assert
        mock_print_warning.assert_called_once()
        assert "Resource assignment cancelled" in mock_print_warning.call_args[0][0]
        mock_questionary_print.assert_not_called()
        mock_confirm.assert_called()

        # Reset mock
        mock_print_warning.reset_mock()
        mock_questionary_print.reset_mock()

        # Assert - check capacity is still unassign
        get(workspace_without_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id not in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_assign_capacity_item_not_supported_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        test_data: StaticTestData,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"

        # Execute command
        cli_executor.exec_command(
            f"assign {capacity_full_path} --workspace {lakehouse.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_assign_domain_workspace_success(
        self,
        virtual_workspace_item_factory,
        workspace_factory,
        mock_questionary_print,
        cli_executor,
    ):
        # Setup
        workspace = workspace_factory()
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"assign {domain.full_path} --workspace {workspace.full_path} --force"
        )

        # Assert
        get(domain.full_path, query="domainWorkspaces")
        assert any(
            workspace.display_name in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_assign_domain_item_not_supported_failure(
        self,
        virtual_workspace_item_factory,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Execute command
        cli_executor.exec_command(
            f"assign {domain.full_path} --workspace {lakehouse.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    # endregion


# region Helper Methods


def unassign(path, workspace, force=True):
    args = _build_unassign_args(path, workspace, force)
    context = handle_context.get_command_context(args.path)
    to_context = handle_context.get_command_context(args.workspace)
    fab_unassign.exec_command(args, context, to_context)


def _build_unassign_args(path, workspace, force):
    return argparse.Namespace(
        command="unassign",
        command_path="unassign",
        path=path,
        workspace=workspace,
        force=force,
    )


def get(path, output=None, query=None):
    args = _build_get_args(path, output, query)
    context = handle_context.get_command_context(args.path)
    fab_fs_get.exec_command(args, context)


def _build_get_args(path, output=None, query=None):
    return argparse.Namespace(
        command="get",
        command_path="get",
        path=path,
        output=output,
        query=[query] if query else None,
        deep_traversal=False,
    )


# endregion
