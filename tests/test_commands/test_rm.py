# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import time
from calendar import c
from unittest.mock import patch

import pytest

import fabric_cli.commands.fs.fab_fs_get as fab_get
import fabric_cli.commands.fs.fab_fs_mkdir as fab_mkdir
import fabric_cli.commands.fs.fab_fs_rm as fab_rm
import fabric_cli.core.fab_state_config as state_config
from fabric_cli.client import (
    fab_api_item,
    fab_api_managedidentity,
    fab_api_managedprivateendpoint,
)
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType, VirtualItemContainerType
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.data.static_test_data import StaticTestData
from tests.test_commands.processors import generate_random_string
from tests.test_commands.utils import cli_path_join


class TestRM:
    # region ITEM
    def test_rm_item_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {notebook.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [notebook.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [notebook.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(notebook.full_path)

    def test_rm_item_without_force_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)
        # Reset mocks
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(f"rm {notebook.full_path}")

        # Assert
        mock_confirm.assert_called_once()
        mock_questionary_print.assert_called_once()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [notebook.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [notebook.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(notebook.full_path)

    def test_rm_item_without_force_cancel_operation_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        mock_print_warning,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)
        # Reset mocks
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False

            # Execute command
            cli_executor.exec_command(f"rm {notebook.full_path}")

        # Assert
        mock_print_warning.assert_called_once()
        mock_confirm.assert_called_once()
        mock_questionary_print.assert_not_called()
        mock_print_done.assert_not_called()

    # endregion

    # region WORKSPACE
    def test_rm_workspace_force_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        workspace = set_entity_metadata(vcr_instance, cassette_name, "Workspace", "/")
        mkdir(
            workspace.full_path,
            params=[f"capacityName={test_data.capacity.name}"],
        )

        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)

        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {workspace.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            ["This will delete 1 underlying items"],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            [workspace.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [workspace.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(workspace.full_path)
        _assert_not_found(notebook.full_path)

    def test_rm_workspace_tenant_level_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        workspace = set_entity_metadata(vcr_instance, cassette_name, "Workspace", "/")
        mkdir(
            workspace.full_path,
            params=[f"capacityName={test_data.capacity.name}"],
        )

        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)

        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):

            mock_checkbox.return_value.ask.return_value = [
                workspace.name,
            ]
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(f"rm . --force")

            # Assert
            mock_print_warning.assert_called()
            mock_questionary_print.assert_called()
            mock_print_done.assert_called()

            assert any(
                str(f"Deleting '{workspace.name}'") in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert (
                "1 workspaces deleted successfully" in mock_print_done.call_args[0][0]
            )

            _assert_not_found(workspace.full_path)
            _assert_not_found(notebook.full_path)

    def test_rm_workspace_without_force_success(
        self,
        workspace_factory,
        item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        workspace = workspace_factory()
        lakehouse = item_factory(ItemType.LAKEHOUSE, workspace.full_path)
        notebook = set_entity_metadata(
            vcr_instance, cassette_name, "Notebook", workspace.full_path
        )
        mkdir(notebook.full_path)
        mock_print_done.reset_mock()

        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):

            mock_checkbox.return_value.ask.return_value = [
                notebook.display_name + ".Notebook"
            ]
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(f"rm {workspace.full_path}")

            # Assert
            mock_questionary_print.assert_called()
            mock_print_done.assert_called()
            _assert_strings_in_mock_calls(
                ["1 items deleted successfully"], True, mock_print_done.mock_calls
            )
            _assert_strings_in_mock_calls(
                [notebook.display_name], True, mock_print_done.mock_calls
            )
            _assert_strings_in_mock_calls(
                [lakehouse.display_name], False, mock_questionary_print.mock_calls
            )

            _assert_not_found(notebook.full_path)
            _assert_found(lakehouse.full_path)

    def test_rm_empty_workspace_without_force_failure(
        self,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        workspace = set_entity_metadata(vcr_instance, cassette_name, "Workspace", "/")
        mkdir(
            workspace.full_path,
            params=[f"capacityName={test_data.capacity.name}"],
        )

        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {workspace.full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_NOT_SUPPORTED, "Empty workspace. Use -f to remove it"
        )

        # Cleanup
        rm(workspace.full_path, force=True)

    # endregion

    # region SparkPool
    def test_rm_spark_pool_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        sparkpool_display_name = generate_random_string(vcr_instance, cassette_name)
        sparkpool_name = f"{sparkpool_display_name}.SparkPool"
        sparkpool_full_path = cli_path_join(
            workspace.full_path, ".sparkpools", sparkpool_name
        )
        sparkpool = EntityMetadata(
            sparkpool_display_name, sparkpool_name, sparkpool_full_path
        )
        mkdir(sparkpool.full_path)

        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {sparkpool.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [sparkpool.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [sparkpool.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(sparkpool.full_path)

    # endregion

    # region ManagedIdentity
    def test_rm_managed_identity_success(
        self,
        virtual_item_factory,
        cli_executor,
        delete_managed_identity_from_cache,
        spy_deprovision_managed_identity,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        managed_identity = virtual_item_factory(
            VirtualItemContainerType.MANAGED_IDENTITY, should_clean=False
        )
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {managed_identity.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        spy_deprovision_managed_identity.assert_called_once()
        delete_managed_identity_from_cache.assert_called_once()

        _assert_strings_in_mock_calls(
            [managed_identity.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [managed_identity.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(managed_identity.full_path)

    # endregion

    # region ManagedPrivateEndpoint
    def test_rm_managed_private_endpoint_success(
        self,
        virtual_item_factory,
        cli_executor,
        delete_managed_private_endpoint_from_cache,
        spy_delete_managed_private_endpoint,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        managed_private_endpoint = virtual_item_factory(
            VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT, should_clean=False
        )
        # Managed private endpoint could take a while to be provisioned - API GAP
        time.sleep(120)
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {managed_private_endpoint.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        spy_delete_managed_private_endpoint.assert_called_once()
        delete_managed_private_endpoint_from_cache.assert_called_once()

        _assert_strings_in_mock_calls(
            [managed_private_endpoint.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            [managed_private_endpoint.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(managed_private_endpoint.full_path)

    # endregion

    # region ExternalDataShare
    def test_rm_external_data_share_success(
        self,
        virtual_item_factory,
        cli_executor,
        delete_external_data_share_from_cache,
        spy_revoke_item_external_data_share,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        external_data_share = virtual_item_factory(
            VirtualItemContainerType.EXTERNAL_DATA_SHARE, should_clean=False
        )
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {external_data_share.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        spy_revoke_item_external_data_share.assert_called_once()
        delete_external_data_share_from_cache.assert_called_once()

        _assert_strings_in_mock_calls(
            [external_data_share.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [external_data_share.display_name], True, mock_print_done.mock_calls
        )

    # endregion

    # region Capacity
    def test_rm_capacity_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        setup_config_values_for_capacity,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        capacity = set_entity_metadata(
            vcr_instance, cassette_name, "Capacity", ".capacities"
        )
        mkdir(capacity.full_path)

        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {capacity.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [capacity.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [capacity.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(capacity.full_path)

    # endregion

    # region Domain
    def test_rm_domain_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        domain = set_entity_metadata(vcr_instance, cassette_name, "Domain", ".domains")
        mkdir(domain.full_path)

        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {domain.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [domain.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [domain.display_name], True, mock_print_done.mock_calls
        )

        _assert_not_found(domain.full_path)

    # endregion

    # region Connection
    def test_rm_connection_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        connection = set_entity_metadata(
            vcr_instance, cassette_name, "Connection", ".connections"
        )

        mkdir(
            connection.full_path,
            params=[
                f"connectionDetails.type=SQL,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
            ],
        )

        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {connection.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [connection.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [f"'{connection.name}' deleted"], True, mock_print_done.mock_calls
        )

        _assert_not_found(connection.full_path)

    # endregion

    # region Gateway
    def test_rm_gateway_success(
        self,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        gateway = set_entity_metadata(
            vcr_instance, cassette_name, "Gateway", ".gateways"
        )

        mkdir(
            gateway.full_path,
            params=[
                f"capacity={test_data.capacity.name},virtualNetworkName={test_data.vnet.name},subnetName={test_data.vnet.subnet}"
            ],
        )

        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {gateway.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [gateway.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [f"'{gateway.name}' deleted"], True, mock_print_done.mock_calls
        )

        _assert_not_found(gateway.full_path)

    # endregion

    # region Folders

    def test_rm_folder_success(
        self,
        folder_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        folder = folder_factory(should_clean=False)
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {folder.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [folder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [f"'{folder.name}' deleted"], True, mock_print_done.mock_calls
        )

        _assert_not_found(folder.full_path)

    def test_rm_non_empty_folder_failure(
        self,
        folder_factory,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        folder = folder_factory(should_clean=False)
        lakehouse = item_factory(
            ItemType.LAKEHOUSE, folder.full_path, should_clean=False
        )
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {folder.full_path} --force")

        # Assert
        assert_fabric_cli_error("FolderNotEmpty", "The requested folder was not empty")

        # Cleanup
        rm(lakehouse.full_path, force=True)
        time.sleep(3)
        rm(folder.full_path, force=True)

    def test_rm_subfolder_success(
        self,
        folder_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_warning,
        mock_print_done,
    ):
        # Setup
        folder = folder_factory(should_clean=True)
        subfolder = folder_factory(path=folder.full_path, should_clean=False)
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"rm {subfolder.full_path} --force")

        # Assert
        mock_print_warning.assert_called()
        mock_questionary_print.assert_called()
        mock_print_done.assert_called_once()
        _assert_strings_in_mock_calls(
            [subfolder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            [f"'{subfolder.name}' deleted"], True, mock_print_done.mock_calls
        )

        _assert_not_found(subfolder.full_path)

    # endregion


# region Helper Methods
def rm(path, force=True):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_rm_args(path, force)
    context = handle_context.get_command_context(args.path)
    fab_rm.exec_command(args, context)


def _build_rm_args(path, force):
    return argparse.Namespace(command="rm", command_path="rm", path=path, force=force)


def mkdir(path, params=["run=true"]):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_mkdir_args(path, params)
    context = handle_context.get_command_context(args.path, False)
    fab_mkdir.exec_command(args, context)


def _build_mkdir_args(path, params):
    return argparse.Namespace(
        command="mkdir", command_path="mkdir", path=path, params=params
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


def _assert_not_found(full_path: str, status_code=constant.ERROR_NOT_FOUND):
    with pytest.raises(FabricCLIError) as e:
        get(full_path)

    if status_code:
        assert e.value.status_code == status_code


def _assert_found(full_path: str):
    try:
        get(full_path)
    except FabricCLIError as e:
        pytest.fail(f"Expected {full_path} to exist, but got error: {e}")


def set_entity_metadata(vcr_instance, cassette_name, type, path=""):
    display_name = generate_random_string(vcr_instance, cassette_name)
    name = f"{display_name}.{type}"
    full_path = cli_path_join(path, name)
    entity = EntityMetadata(display_name, name, full_path)

    return entity


def _assert_strings_in_mock_calls(
    strings: list[str],
    should_exist: bool,
    mock_calls,
    require_all_in_same_args: bool = False,
):
    """
    Assert that specified strings are present or absent in the mock calls based on flags.

    Args:
        strings (list[str]): List of strings to check in the mock calls.
        should_exist (bool): If True, assert strings are in the mock calls; if False, assert they are not.
        mock_calls (list): List of mock call arguments to verify.
        require_all_in_same_args (bool): If True, checks that all strings exist together in the same `args`.

    Raises:
        AssertionError: If the assertion fails.
    """
    if require_all_in_same_args:
        # Check if all strings exist together in the same call.args[0]
        match_found = any(
            all(string in call.args[0] for string in strings) for call in mock_calls
        )
    else:
        # Check if each string exists independently across the mock calls
        match_found = all(
            any(string in call.args[0] for call in mock_calls) for string in strings
        )

    if should_exist:
        assert (
            match_found
        ), f"Expected strings {strings} to {'all be present together' if require_all_in_same_args else 'be present'} in the mock calls, but they were not found."
    else:
        assert (
            not match_found
        ), f"Expected strings {strings} to {'not all be present together' if require_all_in_same_args else 'not be present'} in the mock calls, but they were found."


@pytest.fixture()
def delete_managed_identity_from_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.delete_managed_identity_from_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def spy_deprovision_managed_identity():
    with patch(
        "fabric_cli.client.fab_api_managedidentity.deprovision_managed_identity",
        side_effect=fab_api_managedidentity.deprovision_managed_identity,
    ) as mock:
        yield mock


@pytest.fixture()
def delete_managed_private_endpoint_from_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.delete_managed_private_endpoint_from_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def spy_delete_managed_private_endpoint():
    with patch(
        "fabric_cli.client.fab_api_managedprivateendpoint.delete_managed_private_endpoint",
        side_effect=fab_api_managedprivateendpoint.delete_managed_private_endpoint,
    ) as mock:
        yield mock


@pytest.fixture()
def delete_external_data_share_from_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.delete_external_data_share_from_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def spy_revoke_item_external_data_share():
    with patch(
        "fabric_cli.client.fab_api_item.revoke_item_external_data_share",
        side_effect=fab_api_item.revoke_item_external_data_share,
    ) as mock:
        yield mock


# endregion
