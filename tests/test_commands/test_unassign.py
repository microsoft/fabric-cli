# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import patch

import pytest

import fabric_cli.commands.fs.fab_fs_assign as fab_assign
import fabric_cli.commands.fs.fab_fs_unassign as fab_unassign
from fabric_cli.commands.fs import fab_fs_get
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType
from tests.test_commands.data.static_test_data import StaticTestData


class TestUnassign:
    # region Parametrized Tests
    # @pytest.mark.parametrize("entity_type,factory_key,path_template,assertion_key", [
    #     (VirtualWorkspaceType.CAPACITY, "test_data", "/.capacities/{}.Capacity", "id"),
    #     (VirtualWorkspaceType.DOMAIN, "virtual_workspace_item_factory", "{}.full_path", "display_name"),
    # ])
    # def test_unassign_entity_workspace_success(
    #     self,
    #     entity_type,
    #     factory_key,
    #     path_template,
    #     assertion_key,
    #     workspace_factory,
    #     cli_executor,
    #     mock_questionary_print,
    #     test_data: StaticTestData,
    #     virtual_workspace_item_factory,
    # ):
    #     # Setup
    #     workspace = workspace_factory()
    #     mock_questionary_print.reset_mock()

    #     if factory_key == "test_data":
    #         # Capacity scenario
    #         entity_path = path_template.format(test_data.capacity.name)
    #         assertion_value = getattr(test_data.capacity, assertion_key)
    #     else:
    #         # Domain scenario
    #         domain = virtual_workspace_item_factory(entity_type)
    #         assign(domain.full_path, workspace.full_path)
    #         entity_path = domain.full_path
    #         assertion_value = getattr(domain, assertion_key)

    #     # Execute command
    #     cli_executor.exec_command(
    #         f"unassign {entity_path} --workspace {workspace.full_path} --force"
    #     )

    #     # Assert
    #     if entity_type == VirtualWorkspaceType.CAPACITY:
    #         get(workspace.full_path, query=".")
    #     else:
    #         get(entity_path, query="domainWorkspaces")
    #
    #     assert any(
    #         str(assertion_value) not in str(call.args[0])
    #         for call in mock_questionary_print.mock_calls
    #     )

    # @pytest.mark.parametrize("entity_type,factory_key,path_template", [
    #     (VirtualWorkspaceType.CAPACITY, "test_data", "/.capacities/{}.Capacity"),
    #     (VirtualWorkspaceType.DOMAIN, "virtual_workspace_item_factory", "{}.full_path"),
    # ])
    # def test_unassign_entity_workspace_not_assigned_failure(
    #     self,
    #     entity_type,
    #     factory_key,
    #     path_template,
    #     workspace_factory,
    #     cli_executor,
    #     assert_fabric_cli_error,
    #     test_data: StaticTestData,
    #     virtual_workspace_item_factory,
    # ):
    #     # Setup
    #     workspace = workspace_factory()
    #
    #     if factory_key == "test_data":
    #         # Capacity scenario - ensure it's unassigned first
    #         entity_path = path_template.format(test_data.capacity.name)
    #         unassign(entity_path, workspace.full_path)
    #     else:
    #         # Domain scenario - just create domain without assigning
    #         domain = virtual_workspace_item_factory(entity_type)
    #         entity_path = domain.full_path

    #     # Execute command
    #     cli_executor.exec_command(
    #         f"unassign {entity_path} --workspace {workspace.full_path} --force"
    #     )

    #     # Assert
    #     assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    # @pytest.mark.parametrize("entity_type,factory_key,path_template", [
    #     (VirtualWorkspaceType.CAPACITY, "test_data", "/.capacities/{}.Capacity"),
    #     (VirtualWorkspaceType.DOMAIN, "virtual_workspace_item_factory", "{}.full_path"),
    # ])
    # def test_unassign_entity_item_not_supported_failure(
    #     self,
    #     entity_type,
    #     factory_key,
    #     path_template,
    #     item_factory,
    #     cli_executor,
    #     assert_fabric_cli_error,
    #     test_data: StaticTestData,
    #     virtual_workspace_item_factory,
    # ):
    #     # Setup
    #     lakehouse = item_factory(ItemType.LAKEHOUSE)
    #
    #     if factory_key == "test_data":
    #         entity_path = path_template.format(test_data.capacity.name)
    #     else:
    #         domain = virtual_workspace_item_factory(entity_type)
    #         entity_path = domain.full_path

    #     # Execute command
    #     cli_executor.exec_command(
    #         f"unassign {entity_path} --workspace {lakehouse.full_path} --force"
    #     )

    #     # Assert
    #     assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    # endregion

    # region CAPACITY TESTS
    def test_unassign_capacity_workspace_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_with_capacity = workspace_factory()
        mock_questionary_print.reset_mock()

        # Execute command
        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        cli_executor.exec_command(
            f"unassign {capacity_full_path} --workspace {workspace_with_capacity.full_path} --force"
        )

        # Assert
        get(workspace_with_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id not in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_unassign_capacity_workspace_without_force_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_with_capacity = workspace_factory()
        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            # Execute command
            cli_executor.exec_command(
                f"unassign {capacity_full_path} --workspace {workspace_with_capacity.full_path}"
            )

        # Assert
        mock_confirm.assert_called_once()
        get(workspace_with_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id not in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_unassign_capacity_workspace_without_force_cancel_operation_success(
        self,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        test_data: StaticTestData,
    ):
        # Setup
        workspace_with_capacity = workspace_factory()
        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        capacity_full_path = f"/.capacities/{test_data.capacity.name}.Capacity"
        with patch("questionary.confirm") as mock_confirm:
            # simulate user cancel the operation
            mock_confirm.return_value.ask.return_value = False
            # Execute command
            cli_executor.exec_command(
                f"unassign {capacity_full_path} --workspace {workspace_with_capacity.full_path}"
            )

        # Assert
        mock_print_warning.assert_called_once()
        mock_questionary_print.assert_not_called()
        mock_confirm.assert_called()  # force is disabled

        # Reset mock
        mock_questionary_print.reset_mock()

        # Assert - check capacity is still assigned
        get(workspace_with_capacity.full_path, query=".")
        assert any(
            test_data.capacity.id in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

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


def assign(path, workspace, force=True):
    args = _build_assign_args(path, workspace, force)
    context = handle_context.get_command_context(args.path)
    to_context = handle_context.get_command_context(args.workspace)
    fab_assign.exec_command(args, context, to_context)


def _build_assign_args(path, workspace, force):
    return argparse.Namespace(
        command="assign",
        command_path="assign",
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
