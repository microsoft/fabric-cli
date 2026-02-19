# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import os
import time

import pytest

import fabric_cli.core.fab_state_config as state_config
from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_output import OutputStatus
from fabric_cli.core.fab_types import (
    ItemType,
    VirtualItemContainerType,
    VirtualWorkspaceType,
)
from fabric_cli.errors import ErrorMessages
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.data.static_test_data import StaticTestData
from tests.test_commands.utils import cli_path_join


class TestLS:

    _workspace_long_columns = [
        "name",
        "id",
        "capacityName",
        "capacityId",
        "capacityRegion",
    ]
    _virtual_workspaces = [vws.value for vws in VirtualWorkspaceType]

    _workspace_items_long_columns = ["name", "id"]
    _virtual_workspace_items = [vws.value for vws in VirtualItemContainerType]

    _item_folders_long_columns = ["permissions", "lastModified", "name"]

    _capacity_long_columns = [
        "name",
        "id",
        "sku",
        "region",
        "state",
        "subscriptionId",
        "resourceGroup",
        "admins",
        "tags",
    ]

    _domain_long_columns = ["id", "contributorsScope",
                            "description", "parentDomainId"]

    _connection_long_columns = [
        "name",
        "id",
        "type",
        "connectivityType",
        "gatewayName",
        "gatewayId",
        "privacyLevel",
    ]

    _gateways_long_columns = [
        "name",
        "id",
        "type",
        "capacityId",
        "numberOfMemberGateways",
        "version",
    ]
    _sparkpools_long_columns = [
        "id",
        "nodeFamily",
        "nodeSize",
        "type",
        "autoScale",
        "dynamicExecutorAllocation",
    ]

    _managed_identities_long_columns = [
        "name", "servicePrincipalId", "applicationId"]

    _managed_private_endpoints_long_columns = [
        "name",
        "id",
        "connectionState",
        "provisioningState",
        "targetPrivateLinkResourceId",
        "targetSubresourceType",
    ]

    _external_data_shares_long_columns = [
        "name",
        "id",
        "status",
        "itemId",
    ]

    # region ITEM
    @pytest.mark.parametrize("command", ["ls", "dir"])
    def test_ls_workspace_items_success(
        self,
        workspace,
        item_factory,
        mock_questionary_print,
        command,
        cli_executor: CLIExecutor,
    ):
        # Setup 3 items
        notebook = item_factory(ItemType.NOTEBOOK)
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE)

        # Test 1: without args
        cli_executor.exec_command(f"{command} {workspace.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspace_items, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"{command} {workspace.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspace_items, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 3: with all
        cli_executor.exec_command(f"{command} {workspace.full_path} --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspace_items, True, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 4: with all and long
        cli_executor.exec_command(
            f"{command} {workspace.full_path} --long --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspace_items, True, mock_questionary_print.mock_calls
        )

    def test_ls_query_filter_success(
        self,
        workspace,
        item_factory,
        mock_questionary_print,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup items with different names and types
        notebook1 = item_factory(ItemType.NOTEBOOK)
        notebook2 = item_factory(ItemType.NOTEBOOK)
        notebook3 = item_factory(ItemType.NOTEBOOK)

        # Test 1: Basic JMESPath syntax
        cli_executor.exec_command(f"ls {workspace.full_path} -q [].name")
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook1.display_name, notebook2.display_name, notebook3.display_name],
            True,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 2: JMESPath object syntax
        cli_executor.exec_command(
            f"ls {workspace.full_path} -l -q '[].{{displayName: name, itemID: id}}'"
        )
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook1.display_name, notebook2.display_name, notebook3.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        # Verify renamed fields
        _assert_strings_in_mock_calls(
            ["displayName", "itemID"],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

        mock_questionary_print.reset_mock()

        # Test 3: JMESPath list syntax - here there are not keys so will be printed as list of arrays
        cli_executor.exec_command(f"ls {workspace.full_path} -q [].[name]")
        _assert_strings_in_mock_calls(
            [f"['{notebook1.name}']", f"['{notebook2.name}']",
                f"['{notebook3.name}']"],
            True,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 4: JMESPath object syntax without -l should not have id in the result
        cli_executor.exec_command(
            f'ls {workspace.full_path} -q "[].{{displayName: name, itemId: id}}"')
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [f'{notebook1.name}   None', f'{notebook2.name}   None',
                f'{notebook3.name}   None'],
            True,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 5: JMESPath query filters specific value
        cli_executor.exec_command(
            f"ls {workspace.full_path} -q \"[?name=='{notebook1.name}'].name\""
        )
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [f"{notebook1.name}"],
            True,
            mock_questionary_print.mock_calls,
        )

        _assert_strings_in_mock_calls(
            [f"{notebook2.name}", f"{notebook3.name}"],
            False,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 6: Invalid query format
        cli_executor.exec_command(f'ls {workspace.full_path} -q "name type"')
        assert_fabric_cli_error(
            fab_constant.ERROR_INVALID_INPUT, ErrorMessages.Common.invalid_jmespath_query())

    def test_ls_item_show_hidden_from_config_success(
        self,
        item_factory,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        mock_fab_set_state_config,
    ):
        # Setup
        mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "json")
        mock_fab_set_state_config(fab_constant.FAB_SHOW_HIDDEN, "true")
        notebook = item_factory(ItemType.NOTEBOOK)
        mock_questionary_print.reset_mock()

        # Test: ls without --all flag but with FAB_SHOW_HIDDEN=true config
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        actual_json = json.loads(mock_questionary_print.mock_calls[0].args[0])

        # Check hidden_data is present despite no --all flag
        assert actual_json["result"]["hidden_data"] is not None
        expected_hidden_data_keys = [
            vws.value for vws in VirtualItemContainerType]
        for key in expected_hidden_data_keys:
            assert any(key in k for k in actual_json["result"]["hidden_data"])

    def test_ls_item_json_format_success(
        self,
        item_factory,
        workspace,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        mock_fab_set_state_config,
    ):
        # Setup
        mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "json")
        notebook = item_factory(ItemType.NOTEBOOK)

        mock_questionary_print.reset_mock()

        # Test 1: without args
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_output_json_format_response(
            json.loads(mock_questionary_print.mock_calls[0].args[0])
        )
        mock_questionary_print.reset_mock()

        # Test 2: with all and long
        cli_executor.exec_command(f"ls {workspace.full_path} --long --all")

        # Assert
        mock_questionary_print.assert_called()

        actual_json = json.loads(mock_questionary_print.mock_calls[0].args[0])
        # check --all flag
        assert actual_json["result"]["hidden_data"] is not None
        expected_hidden_data_keys = [
            vws.value for vws in VirtualItemContainerType]
        for key in expected_hidden_data_keys:
            assert any(key in k for k in actual_json["result"]["hidden_data"])

        # check --long flag
        expected_keys = {"name", "id"}
        assert expected_keys.issubset(actual_json["result"]["data"][0].keys())

    # endregion

    # region WORKSPACE
    def test_ls_workspaces_success(
        self,
        workspace,
        mock_questionary_print,
        mock_fab_set_state_config,
        cli_executor: CLIExecutor,
        test_data: StaticTestData,
    ):
        # Test 1: without args
        cli_executor.exec_command("ls")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [workspace.display_name],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._workspace_long_columns, False, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspaces, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command("ls --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [
                workspace.display_name,
                test_data.capacity.id,
                test_data.capacity.name,
            ],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._workspace_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspaces, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 3: with all
        cli_executor.exec_command("ls --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [workspace.display_name],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._workspace_long_columns, False, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspaces, True, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 4: with all and long
        cli_executor.exec_command("ls --long --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [
                workspace.display_name,
                test_data.capacity.id,
                test_data.capacity.name,
            ],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._workspace_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspaces, True, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 5: with --output_format flag to override output format
        cli_executor.exec_command("ls --output_format json")

        # Verify JSON output despite text config
        actual_json = json.loads(mock_questionary_print.mock_calls[0].args[0])
        assert isinstance(actual_json, dict)
        assert "result" in actual_json
        assert "data" in actual_json["result"]

        mock_questionary_print.reset_mock()

        # Test 6: with --output_format flag to override output format from json to text
        mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "json")
        cli_executor.exec_command("ls --output_format text")

        # Verify text output despite json config
        with pytest.raises(json.JSONDecodeError):
            json.loads(mock_questionary_print.mock_calls[0].args[0])

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [workspace.display_name],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._workspace_long_columns, False, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._virtual_workspaces, False, mock_questionary_print.mock_calls
        )

    def test_ls_workspaces_json_format_success(
        self,
        workspace,
        mock_questionary_print,
        mock_fab_set_state_config,
        cli_executor: CLIExecutor,
    ):
        # Setup
        mock_fab_set_state_config(fab_constant.FAB_OUTPUT_FORMAT, "json")

        # Test 1: without args
        cli_executor.exec_command("ls")

        # Assert
        mock_questionary_print.assert_called()
        _assert_output_json_format_response(
            json.loads(mock_questionary_print.mock_calls[0].args[0])
        )

        # Reset mock
        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command("ls --long")

        # Assert
        mock_questionary_print.assert_called()

        actual_json = json.loads(mock_questionary_print.mock_calls[0].args[0])
        assert "hidden_data" not in actual_json["result"]

        # check header fields are present
        expected_keys = {
            "name",
            "id",
            "capacityName",
            "capacityId",
            "capacityRegion",
        }
        assert expected_keys.issubset(actual_json["result"]["data"][0].keys())

        # Reset mock
        mock_questionary_print.reset_mock()

        # Test 3: with all
        cli_executor.exec_command("ls -a")

        # Assert
        mock_questionary_print.assert_called()

        actual_json = json.loads(mock_questionary_print.mock_calls[0].args[0])
        # check --all flag adds hidden_data
        assert actual_json["result"]["hidden_data"] is not None
        expected_hidden_data_keys = [vws.value for vws in VirtualWorkspaceType]
        for key in expected_hidden_data_keys:
            assert any(key in k for k in actual_json["result"]["hidden_data"])

    # endregion

    # region ITEM FOLDERS
    @pytest.mark.parametrize("item_type, expected_folders", 
                             [(ItemType.LAKEHOUSE, ["Files", "Tables", "TableMaintenance"]),
                              (ItemType.COSMOS_DB_DATABASE, ["Files", "Tables", "Code", "Audit"])])
    def test_ls_item_folders_success(
        self, item_type, expected_folders, item_factory, mock_questionary_print, cli_executor: CLIExecutor
    ):
        # Setup
        item = item_factory(item_type)
        expected_output = expected_folders

        # Test 1: without args
        cli_executor.exec_command(f"ls {item.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            expected_output, True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._item_folders_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {item.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            expected_output, True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._item_folders_long_columns, True, mock_questionary_print.mock_calls
        )

    # endregion

    # region SparkPool
    def test_ls_spark_pool_success(
        self,
        workspace,
        virtual_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        sparkpool = virtual_item_factory(VirtualItemContainerType.SPARK_POOL)
        sparkpools_path = cli_path_join(
            workspace.full_path, str(VirtualItemContainerType.SPARK_POOL)
        )

        mock_questionary_print.reset_mock()

        # Test 1: without args
        cli_executor.exec_command(f"ls {sparkpools_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [sparkpool.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._sparkpools_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {sparkpools_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [sparkpool.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._sparkpools_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region ManagedIdentities
    def test_ls_managed_identities_success(
        self,
        workspace,
        virtual_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        managed_identity = virtual_item_factory(
            VirtualItemContainerType.MANAGED_IDENTITY
        )
        managed_identities_path = cli_path_join(
            workspace.full_path, str(VirtualItemContainerType.MANAGED_IDENTITY)
        )
        # Test 1: without args
        cli_executor.exec_command(f"ls {managed_identities_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [managed_identity.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._managed_identities_long_columns,
            False,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {managed_identities_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [managed_identity.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._managed_identities_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region ManagedPrivateEndpoints
    def test_ls_managed_private_endpoints_success(
        self,
        workspace,
        virtual_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        managed_private_endpoint = virtual_item_factory(
            VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        )
        managed_private_endpoints_path = cli_path_join(
            workspace.full_path, str(
                VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT)
        )

        mock_questionary_print.reset_mock()

        # Test 1: without args
        cli_executor.exec_command(f"ls {managed_private_endpoints_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [managed_private_endpoint.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._managed_private_endpoints_long_columns,
            False,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(
            f"ls {managed_private_endpoints_path} --long")
        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [managed_private_endpoint.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._managed_private_endpoints_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        # Wait time for removal
        time.sleep(120)

    # endregion

    # region ExternalDataShares
    def test_ls_external_data_shares_success(
        self,
        workspace,
        virtual_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        external_data_share = virtual_item_factory(
            VirtualItemContainerType.EXTERNAL_DATA_SHARE
        )
        external_data_shares_path = cli_path_join(
            workspace.full_path, str(
                VirtualItemContainerType.EXTERNAL_DATA_SHARE)
        )
        # Test 1: without args
        cli_executor.exec_command(f"ls {external_data_shares_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [external_data_share.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._external_data_shares_long_columns,
            False,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {external_data_shares_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [external_data_share.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._external_data_shares_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    def test_ls_external_data_shares_use_cache_success(
        self,
        workspace,
        virtual_item_factory,
        mock_questionary_print,
        mock_fab_set_state_config,
        cli_executor: CLIExecutor,
    ):
        # Setup
        external_data_share = virtual_item_factory(
            VirtualItemContainerType.EXTERNAL_DATA_SHARE
        )
        external_data_shares_path = cli_path_join(
            workspace.full_path, str(
                VirtualItemContainerType.EXTERNAL_DATA_SHARE)
        )

        mock_fab_set_state_config(fab_constant.FAB_CACHE_ENABLED, "true")

        # Test 1: without args
        cli_executor.exec_command(f"ls {external_data_shares_path}")

        # Assert
        mock_questionary_print.assert_called()

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [external_data_share.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._external_data_shares_long_columns,
            False,
            mock_questionary_print.mock_calls,
        )

    # endregion

    # region Capacity
    def test_ls_capacity_success(
        self,
        cli_executor: CLIExecutor,
        virtual_workspace_item_factory,
        mock_questionary_print,
        setup_config_values_for_capacity,
        test_data: StaticTestData,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(
            VirtualWorkspaceType.CAPACITY)

        # Test 1: without args
        cli_executor.exec_command(f"ls {str(VirtualWorkspaceType.CAPACITY)}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [capacity.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._capacity_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(
            f"ls {str(VirtualWorkspaceType.CAPACITY)} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [
                capacity.display_name,
                test_data.azure_resource_group,
                test_data.admin.upn,
            ],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._capacity_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region Domain
    def test_ls_domain_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Test 1: without args
        cli_executor.exec_command(f"ls {str(VirtualWorkspaceType.DOMAIN)}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [domain.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._domain_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(
            f"ls {str(VirtualWorkspaceType.DOMAIN)} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [domain.display_name],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._domain_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region Connection
    def test_ls_connection_success(
        self,
        cli_executor: CLIExecutor,
        virtual_workspace_item_factory,
        mock_questionary_print,
    ):
        # Setup
        connection = virtual_workspace_item_factory(
            VirtualWorkspaceType.CONNECTION)

        # Test 1: without args
        cli_executor.exec_command(f"ls {str(VirtualWorkspaceType.CONNECTION)}")
        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [connection.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._connection_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(
            f"ls {str(VirtualWorkspaceType.CONNECTION)} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [
                connection.display_name,
                "SQL",
                "ShareableCloud",
            ],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._connection_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region Gateways
    def test_ls_gateways_success(
        self,
        cli_executor: CLIExecutor,
        virtual_workspace_item_factory,
        mock_questionary_print,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        # Test 1: without args
        cli_executor.exec_command(f"ls {str(VirtualWorkspaceType.GATEWAY)}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [gateway.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._gateways_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(
            f"ls {str(VirtualWorkspaceType.GATEWAY)} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [
                gateway.display_name,
                "VirtualNetwork",
            ],
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )
        _assert_strings_in_mock_calls(
            self._gateways_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    # endregion

    # region Folder

    def test_ls_folder_success(
        self,
        workspace,
        folder_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        folder = folder_factory()

        # Test 1: without args
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [folder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {workspace.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [folder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    def test_ls_subfolder_success(
        self,
        workspace,
        folder_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):

        # Setup
        folder = folder_factory()
        subfolder = folder_factory(path=folder.full_path)

        # Test 1: without args
        cli_executor.exec_command(f"ls {folder.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [subfolder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {folder.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [subfolder.display_name], True, mock_questionary_print.mock_calls
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    def test_ls_folder_content_success(
        self,
        workspace,
        folder_factory,
        item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        folder = folder_factory()

        # Setup 3 items
        notebook = item_factory(ItemType.NOTEBOOK, path=folder.full_path)
        lakehouse = item_factory(ItemType.LAKEHOUSE, path=folder.full_path)
        data_pipeline = item_factory(
            ItemType.DATA_PIPELINE, path=folder.full_path)

        # Test 1: without args
        cli_executor.exec_command(f"ls {folder.full_path}")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long
        cli_executor.exec_command(f"ls {folder.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

        mock_questionary_print.reset_mock()

        # Test 3: with all
        cli_executor.exec_command(f"ls {folder.full_path} --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 4: with all and long
        cli_executor.exec_command(f"ls {folder.full_path} --long --all")

        # Assert
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns,
            True,
            mock_questionary_print.mock_calls,
            require_all_in_same_args=True,
        )

    def test_ls_workspace_with_folders_and_items_divider(
        self,
        workspace,
        folder_factory,
        item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        """Test that a divider appears between folders and items when folder_listing_enabled=true"""
        # Setup: Create folders and items in workspace root
        folder1 = folder_factory()
        folder2 = folder_factory()
        notebook = item_factory(ItemType.NOTEBOOK, path=workspace.full_path)
        lakehouse = item_factory(ItemType.LAKEHOUSE, path=workspace.full_path)

        # Test 1: List workspace (folder_listing_enabled is true by default in tests)
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert: Check that the divider is present
        mock_questionary_print.assert_called()

        # Verify divider appears in output
        _assert_strings_in_mock_calls(
            ["------------------------------"], True, mock_questionary_print.mock_calls
        )

        # Verify folders and items are present
        _assert_strings_in_mock_calls(
            [
                folder1.display_name,
                folder2.display_name,
                notebook.display_name,
                lakehouse.display_name,
            ],
            True,
            mock_questionary_print.mock_calls,
        )

        mock_questionary_print.reset_mock()

        # Test 2: with long flag
        cli_executor.exec_command(f"ls {workspace.full_path} --long")

        # Assert
        mock_questionary_print.assert_called()

        # Verify divider appears with long format
        _assert_strings_in_mock_calls(
            ["------------------------------"], True, mock_questionary_print.mock_calls
        )

        # Verify all items are present
        _assert_strings_in_mock_calls(
            [
                folder1.display_name,
                folder2.display_name,
                notebook.display_name,
                lakehouse.display_name,
            ],
            True,
            mock_questionary_print.mock_calls,
        )

    def test_ls_workspace_items_no_list_folders_support_success(
        self,
        workspace,
        folder_factory,
        item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        folder = folder_factory()

        # Setup 3 items
        notebook = item_factory(ItemType.NOTEBOOK)
        lakehouse = item_factory(ItemType.LAKEHOUSE, path=folder.full_path)
        data_pipeline = item_factory(
            ItemType.DATA_PIPELINE, path=folder.full_path)

        # Test 1: workspace ls
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert that only the notebook and folder are listed
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, folder.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Test 2: Folder ls
        cli_executor.exec_command(f"ls {folder.full_path}")

        # Assert that only the lakehouse and data pipeline are listed
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [lakehouse.display_name, data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        mock_questionary_print.reset_mock()

        # Disable folder support
        state_config.set_config(
            fab_constant.FAB_FOLDER_LISTING_ENABLED, "false")

        # Test 3: workspace ls
        cli_executor.exec_command(f"ls {workspace.full_path}")

        # Assert that only the items are listed
        mock_questionary_print.assert_called()
        _assert_strings_in_mock_calls(
            [notebook.display_name, lakehouse.display_name,
                data_pipeline.display_name],
            True,
            mock_questionary_print.mock_calls,
        )
        _assert_strings_in_mock_calls(
            self._workspace_items_long_columns, False, mock_questionary_print.mock_calls
        )

        # Enable folder support for cleanup
        state_config.set_config(
            fab_constant.FAB_FOLDER_LISTING_ENABLED, "true")

    # endregion

    # region OneLake
    def test_ls_onelake_empty_paths_success(
        self,
        item_factory,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        onelake_path = cli_path_join(lakehouse.full_path, "Files")

        # Execute
        cli_executor.exec_command(f"ls {onelake_path}")

        # Assert
        mock_questionary_print.assert_called()
        call_args = mock_questionary_print.call_args.args[0]
        assert call_args is not None

    # endregion


# region Helper Methods


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


def _assert_output_json_format_response(actual_result: dict):
    expected_json = {
        "status": OutputStatus.Success,
        "command": "ls",
    }

    for key, value in expected_json.items():
        assert actual_result[key] == value

    assert "data" in actual_result["result"]
    assert "hidden_data" not in actual_result["result"]
    assert "message" not in actual_result["result"]
    assert "error_code" not in actual_result


# endregion
