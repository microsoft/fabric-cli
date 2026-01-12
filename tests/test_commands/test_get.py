# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import time

import fabric_cli.commands.fs.fab_fs_get as fab_get
import fabric_cli.commands.fs.fab_fs_ln as fab_ln
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import (
    ItemType,
    VirtualItemContainerType,
    VirtualWorkspaceType,
)
from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.conftest import assert_fabric_cli_error
from tests.test_commands.data.static_test_data import StaticTestData
from tests.test_commands.utils import cli_path_join


class TestGet:
    # region Workspace
    def test_get_workspace_success(
        self, workspace, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Reset mock
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {workspace.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        mock_print_warning.assert_not_called()
        assert "id" in mock_questionary_print.call_args[0][0]
        assert "displayName" in mock_questionary_print.call_args[0][0]
        assert workspace.display_name in mock_questionary_print.call_args[0][0]
        assert "description" in mock_questionary_print.call_args[0][0]
        assert "oneLakeEndpoints" in mock_questionary_print.call_args[0][0]
        assert "managedPrivateEndpoints" in mock_questionary_print.call_args[0][0]
        assert "sparkSettings" in mock_questionary_print.call_args[0][0]
        assert "roleAssignments" in mock_questionary_print.call_args[0][0]

    def test_get_workspace_with_query_failure(
        self, workspace, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Execute command
        cli_executor.exec_command(f"get {workspace.full_path} -q '.nonexistent'")

        # Assert
        assert_fabric_cli_error(
            fab_constant.ERROR_INVALID_INPUT,
            "Invalid jmespath query (https://jmespath.org)",
        )

    def test_get_workspace_query_displayName_success(
        self, workspace, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Reset mock
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {workspace.full_path} --query displayName")

        # Assert
        mock_questionary_print.assert_called_once()
        mock_print_warning.assert_not_called()
        assert workspace.display_name == mock_questionary_print.call_args[0][0]

    # endregion

    # region Item
    def test_get_item_lakehouse_query_all_success(
        self, item_factory, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {lakehouse.full_path} --query . --force")

        # Assert
        mock_questionary_print.assert_called_once()
        mock_print_warning.assert_not_called()  # lakehouse item is called with get item and not get item with definition
        assert lakehouse.display_name in mock_questionary_print.call_args[0][0]

        # Assert lakehouse extended properties are returned
        assert "properties" in mock_questionary_print.call_args[0][0]
        assert "oneLakeTablesPath" in mock_questionary_print.call_args[0][0]
        assert "oneLakeFilesPath" in mock_questionary_print.call_args[0][0]
        assert "sqlEndpointProperties" in mock_questionary_print.call_args[0][0]

    def test_get_item_environment_success(
        self, item_factory, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Setup
        environment = item_factory(ItemType.ENVIRONMENT)

        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {environment.full_path} --query . --force")

        # Assert
        mock_questionary_print.assert_called_once()
        mock_print_warning.assert_not_called()  # enironment item is called with get item and not get item with definition
        assert environment.display_name in mock_questionary_print.call_args[0][0]

        # Assert enviroment extended properties are returned
        assert "properties" in mock_questionary_print.call_args[0][0]
        assert "publishDetails" in mock_questionary_print.call_args[0][0]

        # Assert environment metadata is returned
        assert "connections" in mock_questionary_print.call_args[0][0]
        assert "published" in mock_questionary_print.call_args[0][0]
        assert "staging" in mock_questionary_print.call_args[0][0]

    def test_get_item_mirroreddb_success(
        self, item_factory, cli_executor, mock_questionary_print, mock_print_warning
    ):
        # Setup
        mirroreddb = item_factory(ItemType.MIRRORED_DATABASE)

        # Reset mock
        mock_questionary_print.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {mirroreddb.full_path} --query . --force")

        # Assert
        mock_questionary_print.assert_called_once()
        mock_print_warning.assert_called_once()  # MIRRORED_DATABASE is called with get item with definition
        assert mirroreddb.display_name in mock_questionary_print.call_args[0][0]

        # Assert mirroreddb definition is returned
        assert "definition" in mock_questionary_print.call_args[0][0]

        # Assert mirroreddb metadata is returned
        assert "connections" in mock_questionary_print.call_args[0][0]
        assert "status" in mock_questionary_print.call_args[0][0]
        assert "tablesStatus" in mock_questionary_print.call_args[0][0]

    # endregion

    # region OneLake
    def test_get_onelake_success(
        self, item_factory, cli_executor, mock_questionary_print
    ):
        # Execute command
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        cli_executor.exec_command(f"get {lakehouse.full_path}/Files --query .")

        # Assert
        mock_questionary_print.assert_called()
        assert any(
            "paths" in call.args[0] for call in mock_questionary_print.mock_calls
        )

    def test_get_onelake_shortcut_success(
        self, item_factory, workspace, cli_executor, mock_questionary_print
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)
        workspace_id = _get_id(workspace.full_path, mock_questionary_print)
        lakehouse_2_id = _get_id(lakehouse2.full_path, mock_questionary_print)

        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "testShortcut.Shortcut"
        )
        target_path = cli_path_join(lakehouse2.full_path, "Files")
        ln(shortcut_path, target=target_path)

        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {shortcut_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert '"name": "testShortcut"' in mock_questionary_print.call_args.args[0]
        assert '"type": "OneLake"' in mock_questionary_print.call_args.args[0]
        assert '"path": "Files"' in mock_questionary_print.call_args.args[0]

        # Assert target
        assert (
            f'"itemId": "{lakehouse_2_id}"' in mock_questionary_print.call_args.args[0]
        )
        assert '"path": "Files"' in mock_questionary_print.call_args.args[0]
        assert (
            f'"workspaceId": "{workspace_id}"'
            in mock_questionary_print.call_args.args[0]
        )

    # endregion

    # region Virtual Workspaces
    def test_get_virtual_workspace_capacity_query_all_success(
        self, cli_executor, mock_questionary_print, test_data: StaticTestData
    ):
        # Execute command
        cli_executor.exec_command(
            f"get /.capacities/{test_data.capacity.name}.Capacity --query ."
        )

        # Assert
        mock_questionary_print.assert_called()
        assert any(
            test_data.capacity.name in call.args[0]
            for call in mock_questionary_print.mock_calls
        )

    def test_get_virtual_workspace_domain_success(
        self, virtual_workspace_item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {domain.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert domain.display_name in mock_questionary_print.call_args[0][0]

        # Assert domain metadata is returned
        assert "parentDomainId" not in mock_questionary_print.call_args[0][0]
        assert "contributorsScope" in mock_questionary_print.call_args[0][0]
        assert "domainWorkspaces" in mock_questionary_print.call_args[0][0]

    # endregion

    # region Virtual Items
    def test_get_virtual_item_sparkpool(
        self, virtual_item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        sparkpool = virtual_item_factory(VirtualItemContainerType.SPARK_POOL)

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {sparkpool.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert sparkpool.display_name in mock_questionary_print.call_args[0][0]

    def test_get_virtual_item_managed_private_endpoint(
        self, virtual_item_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        managed_private_endpoint = virtual_item_factory(
            VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        )

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {managed_private_endpoint.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert (
            managed_private_endpoint.display_name
            in mock_questionary_print.call_args[0][0]
        )

        # Wait time for removal
        time.sleep(120)

    def test_get_virtual_item_external_data_share(
        self,
        virtual_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_fab_logger_log_warning,
    ):
        # Setup
        external_data_share = virtual_item_factory(
            VirtualItemContainerType.EXTERNAL_DATA_SHARE
        )

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_fab_logger_log_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {external_data_share.full_path} --query .")

        # Assert
        # Verify call to get was made
        mock_questionary_print.assert_called_once()
        # Verify warning log was made
        mock_fab_logger_log_warning.assert_called_once()

    # endregion

    # region Folder

    def test_get_folder_success(
        self, folder_factory, cli_executor, mock_questionary_print
    ):
        # Setup
        folder = folder_factory()

        # Reset mock
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {folder.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert "id" in mock_questionary_print.call_args[0][0]
        assert "displayName" in mock_questionary_print.call_args[0][0]
        assert "workspaceId" in mock_questionary_print.call_args[0][0]
        assert "parentFolderId" not in mock_questionary_print.call_args[0][0]
        assert folder.display_name in mock_questionary_print.call_args[0][0]

        # Extract the folder id from the response
        json_response = json.loads(mock_questionary_print.call_args[0][0])
        folder_id = json_response["id"]

        subfolder = folder_factory(path=folder.full_path)
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"get {subfolder.full_path} --query .")

        # Assert
        mock_questionary_print.assert_called_once()
        assert "id" in mock_questionary_print.call_args[0][0]
        assert "displayName" in mock_questionary_print.call_args[0][0]
        assert "workspaceId" in mock_questionary_print.call_args[0][0]
        assert (
            f'"parentFolderId": "{folder_id}"' in mock_questionary_print.call_args[0][0]
        )
        assert subfolder.display_name in mock_questionary_print.call_args[0][0]

    # endregion

    def test_metadata_property_query_validation(self):
        """Test the enhanced metadata property validation for nested properties."""
        from fabric_cli.utils.fab_cmd_get_utils import is_metadata_property_query

        # Test exact matches
        assert is_metadata_property_query("properties") is True
        assert is_metadata_property_query("id") is True
        assert is_metadata_property_query("displayName") is True
        assert is_metadata_property_query("description") is True
        
        # Test nested properties - the key enhancement
        assert is_metadata_property_query("properties.connectionString") is True
        assert is_metadata_property_query("properties.nested.value") is True
        assert is_metadata_property_query("displayName.localized") is True
        
        # Test invalid properties
        assert is_metadata_property_query("someField") is False
        assert is_metadata_property_query("definition") is False
        assert is_metadata_property_query("definition.content") is False


# region Helper Methods
def get(path, output=None, query=None, deep_traversal=False, force=False):
    args = _build_get_args(path, output, query, deep_traversal, force)
    context = handle_context.get_command_context(args.path)
    fab_get.exec_command(args, context)


def _build_get_args(path, output=None, query=None, deep_traversal=False, force=False):
    return argparse.Namespace(
        command="get",
        acl_subcommand="get",
        command_path="get",
        path=path,
        output=output,
        query=[query] if query else None,
        deep_traversal=deep_traversal,
        force=force,
    )


def ln(path, type="oneLake", target=None, input=None, force=True):
    args = _build_ln_args(path, type, target, input, force)
    context = handle_context.get_command_context(args.path, False)
    assert isinstance(context, OneLakeItem)
    fab_ln.exec_command(args, context)


def _build_ln_args(path, type, target, input, force):
    return argparse.Namespace(
        command="ln",
        command_path="ln",
        path=path,
        target=target,
        input=[input] if input else None,
        type=type,
        force=force,
    )


def _get_id(path, mock_questionary_print):
    get(path, query="id")
    return mock_questionary_print.call_args[0][0]


# endregion
