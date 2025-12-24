# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import platform
import re
import time
from unittest.mock import patch

import pytest

import fabric_cli.commands.fs.fab_fs_get as fab_get
import fabric_cli.commands.fs.fab_fs_mkdir as fab_mkdir
import fabric_cli.commands.fs.fab_fs_rm as fab_fs_rm
import fabric_cli.core.fab_state_config as state_config
from fabric_cli.client import (
    fab_api_item,
    fab_api_managedidentity,
    fab_api_managedprivateendpoint,
)
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    ItemType,
    VICMap,
    VirtualItemContainerType,
    VirtualWorkspaceType,
)
from fabric_cli.errors import ErrorMessages
from tests.test_commands.conftest import mock_print_done
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.data.static_test_data import StaticTestData
from tests.test_commands.processors import generate_random_string
from tests.test_commands.utils import cli_path_join


class TestMkdir:
    # region ITEM
    def test_mkdir_item_name_already_exists_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Execute command
        cli_executor.exec_command(f"mkdir {lakehouse.full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_EXISTS)

    def test_mkdir_unsupported_item_failure(
        self,
        workspace_factory,
        cli_executor,
        assert_fabric_cli_error,
        vcr_instance,
        cassette_name,
    ):
        workspace = workspace_factory()

        # Create paginatedReport
        paginatedReport_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        paginatedReport_name = (
            f"{paginatedReport_display_name}.{ItemType.PAGINATED_REPORT}"
        )
        paginatedReport_full_path = cli_path_join(
            workspace.full_path, paginatedReport_name
        )
        paginatedReport = EntityMetadata(
            paginatedReport_display_name,
            paginatedReport_name,
            paginatedReport_full_path,
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {paginatedReport.full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_UNSUPPORTED_COMMAND)

    def test_mkdir_lakehouse_with_creation_payload_success(
        self,
        workspace,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_item_to_cache,
    ):
        lakehouse_display_name = generate_random_string(vcr_instance, cassette_name)
        lakehouse_full_path = cli_path_join(
            workspace.full_path, f"{lakehouse_display_name}.{ItemType.LAKEHOUSE}"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {lakehouse_full_path} -P enableSchemas=true")

        # Assert
        upsert_item_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert lakehouse_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(lakehouse_full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert lakehouse_display_name in mock_questionary_print.call_args[0][0]
        assert "defaultSchema" in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(lakehouse_full_path)

    def test_mkdir_kqldatabase_with_creation_payload_success(
        self,
        workspace,
        item_factory,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_item_to_cache,
    ):
        # Setup
        # Create parent eventhouse
        eventhouse = item_factory(ItemType.EVENTHOUSE)
        get(eventhouse.full_path, query="id")
        eventhouse_id = mock_questionary_print.call_args[0][0]
        mock_print_done.reset_mock()
        upsert_item_to_cache.reset_mock()
        kqldatabase_display_name = generate_random_string(vcr_instance, cassette_name)
        kqldatabase_full_path = cli_path_join(
            workspace.full_path, f"{kqldatabase_display_name}.{ItemType.KQL_DATABASE}"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {kqldatabase_full_path} -P eventhouseid={eventhouse_id}"
        )

        # Assert
        upsert_item_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert kqldatabase_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(kqldatabase_full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert kqldatabase_display_name in mock_questionary_print.call_args[0][0]
        assert eventhouse_id in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(kqldatabase_full_path)

    def test_mkdir_kqldatabase_without_creation_payload_success(
        self,
        workspace,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_item_to_cache,
    ):
        # Setup
        kqldatabase_display_name = generate_random_string(vcr_instance, cassette_name)
        kqldatabase_full_path = cli_path_join(
            workspace.full_path, f"{kqldatabase_display_name}.{ItemType.KQL_DATABASE}"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {kqldatabase_full_path}")

        # Assert
        # call_count is 2 because the first call is for the parent eventhouse and the second call is for the kqldatabase
        assert upsert_item_to_cache.call_count == 2
        # print call_count is 1 because we batch the result of the first call for the parent eventhouse and the second call for the kqldatabase
        assert mock_print_done.call_count == 1
        assert any(
            kqldatabase_display_name in call.args[0]
            for call in mock_print_done.mock_calls
        )

        mock_questionary_print.reset_mock()
        eventhouse_full_path = (
            kqldatabase_full_path.removesuffix(".KQLDatabase") + "_auto.Eventhouse"
        )
        get(eventhouse_full_path, query="id")
        eventhouse_id = mock_questionary_print.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(kqldatabase_full_path, query=".")
        mock_questionary_print.assert_called_once()
        assert kqldatabase_display_name in mock_questionary_print.call_args[0][0]
        assert eventhouse_id in mock_questionary_print.call_args[0][0]

        # Cleanup - removing parent eventhouse removes the kqldatabase as well
        rm(eventhouse_full_path)

    # endregion

    # region WORKSPACE
    def test_mkdir_workspace_name_already_exists_failure(
        self, workspace, cli_executor, assert_fabric_cli_error
    ):
        # Execute command
        cli_executor.exec_command(f"mkdir {workspace.full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_EXISTS)

    def test_mkdir_workspace_with_default_capacity_not_set_failure(
        self, cli_executor, assert_fabric_cli_error, vcr_instance, cassette_name
    ):
        # Setup
        fab_default_capacity = state_config.get_config(constant.FAB_DEFAULT_CAPACITY)
        fab_default_capacity_id = state_config.get_config(
            constant.FAB_DEFAULT_CAPACITY_ID
        )

        state_config.set_config(constant.FAB_DEFAULT_CAPACITY, "")
        state_config.set_config(constant.FAB_DEFAULT_CAPACITY_ID, "")
        workspace_display_name = generate_random_string(vcr_instance, cassette_name)
        workspace_full_path = f"/{workspace_display_name}.Workspace"

        # Execute command
        cli_executor.exec_command(f"mkdir {workspace_full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "The specified capacity was not found or is invalid. Please use 'config set default_capacity <capacity_name>' or '-P capacityName=<capacity_name>'",
        )

        # Cleanup
        state_config.set_config(constant.FAB_DEFAULT_CAPACITY, fab_default_capacity)
        state_config.set_config(
            constant.FAB_DEFAULT_CAPACITY_ID, fab_default_capacity_id
        )

    def test_mkdir_workspace_with_default_capacity_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_workspace_to_cache,
        test_data: StaticTestData,
    ):
        self._mkdir_workspace_success(
            mock_print_done,
            mock_questionary_print,
            test_data,
            vcr_instance,
            cassette_name,
            upsert_workspace_to_cache,
            cli_executor,
        )

    def test_mkdir_workspace_with_capacity_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_workspace_to_cache,
        test_data: StaticTestData,
    ):
        self._mkdir_workspace_success(
            mock_print_done,
            mock_questionary_print,
            test_data,
            vcr_instance,
            cassette_name,
            upsert_workspace_to_cache,
            cli_executor,
            capacity_name=test_data.capacity.name,
        )

    def test_mkdir_workspace_no_capacity_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_workspace_to_cache,
        test_data: StaticTestData,
    ):
        self._mkdir_workspace_success(
            mock_print_done,
            mock_questionary_print,
            test_data,
            vcr_instance,
            cassette_name,
            upsert_workspace_to_cache,
            cli_executor,
            capacity_name=constant.FAB_CAPACITY_NAME_NONE,
        )

    def _mkdir_workspace_success(
        self,
        mock_print_done,
        mock_questionary_print,
        test_data: StaticTestData,
        vcr_instance,
        cassette_name,
        upsert_workspace_to_cache,
        cli_executor,
        capacity_name=None,
    ):

        # Setup
        workspace_display_name = generate_random_string(vcr_instance, cassette_name)
        workspace_full_path = f"/{workspace_display_name}.Workspace"

        fab_capacity_name = state_config.get_config(constant.FAB_DEFAULT_CAPACITY)
        fab_capacity_name_id = state_config.get_config(constant.FAB_DEFAULT_CAPACITY_ID)

        # Execute command
        if capacity_name:
            cli_executor.exec_command(
                f"mkdir {workspace_full_path} -P capacityName={capacity_name}"
            )
        else:
            state_config.set_config(
                constant.FAB_DEFAULT_CAPACITY, test_data.capacity.name
            )
            state_config.set_config(
                constant.FAB_DEFAULT_CAPACITY_ID, test_data.capacity.id
            )
            cli_executor.exec_command(f"mkdir {workspace_full_path}")

        # Assert
        upsert_workspace_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert workspace_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(workspace_full_path, query=".")
        assert workspace_display_name in mock_questionary_print.call_args[0][0]

        # Cleanup
        state_config.set_config(constant.FAB_DEFAULT_CAPACITY, fab_capacity_name)
        state_config.set_config(constant.FAB_DEFAULT_CAPACITY_ID, fab_capacity_name_id)
        rm(workspace_full_path)

    # endregion

    # region OneLake
    def test_mkdir_onelake_success(
        self, item_factory, cli_executor, mock_print_done, vcr_instance, cassette_name
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        mock_print_done.reset_mock()
        onelake_display_name = generate_random_string(vcr_instance, cassette_name)
        onelake_full_path = cli_path_join(
            lakehouse.full_path, "Files", f"{onelake_display_name}"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {onelake_full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert onelake_display_name in mock_print_done.call_args[0][0]

        # calling get to make sure the onelake is created
        get(onelake_full_path)

        # Cleanup
        # lakehouse auto clean-up removes the onelake as well

    def test_mkdir_onelake_not_inside_files_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        onelake_full_path = cli_path_join(
            lakehouse.full_path, "Tables", "InvalidOnelake"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {onelake_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_mkdir_onelake_not_inside_lakehouse_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        warehouse = item_factory(ItemType.WAREHOUSE)
        onelake_full_path = cli_path_join(
            warehouse.full_path, "Files", "InvalidOnelake"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {onelake_full_path}")

        # Assert
        assert_fabric_cli_error("OperationNotAllowedOnThePath")

    def test_mkdir_onelake_invalid_pattern_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        onelake_full_path = cli_path_join(
            lakehouse.full_path,
            "Filesfolder",
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {onelake_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_mkdir_onelake_path_is_files_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        onelake_full_path = cli_path_join(
            lakehouse.full_path,
            "Files",
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {onelake_full_path}")

        # Assert
        assert_fabric_cli_error("PathAlreadyExists")  # API returns 409

    # endregion

    # region SparkPool
    def test_mkdir_sparkpool_with_params_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        sparkpool_display_name = generate_random_string(vcr_instance, cassette_name)
        sparkpool_full_path = cli_path_join(
            workspace.full_path, ".sparkpools", sparkpool_display_name + ".SparkPool"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {sparkpool_full_path} -P nodeSize=Medium,autoScale.minNodeCount=2,autoScale.maxNodeCount=5"
        )

        # Assert
        upsert_spark_pool_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert sparkpool_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(sparkpool_full_path, query=".")
        assert (
            f'"name": "{sparkpool_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert '"nodeSize": "Medium"' in mock_questionary_print.call_args[0][0]
        assert '"minNodeCount": 2' in mock_questionary_print.call_args[0][0]
        assert '"maxNodeCount": 5' in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(sparkpool_full_path)

    def test_mkdir_sparkpool_without_params_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        sparkpool_display_name = generate_random_string(vcr_instance, cassette_name)
        sparkpool_full_path = cli_path_join(
            workspace.full_path, ".sparkpools", sparkpool_display_name + ".SparkPool"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {sparkpool_full_path}")

        # Assert
        upsert_spark_pool_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert sparkpool_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(sparkpool_full_path, query=".")
        assert (
            f'"name": "{sparkpool_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert '"nodeSize": "Small"' in mock_questionary_print.call_args[0][0]
        assert '"minNodeCount": 1' in mock_questionary_print.call_args[0][0]
        assert '"maxNodeCount": 1' in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(sparkpool_full_path)

    def test_mkdir_sparkpool_with_params_without_maxNodeCount_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        sparkpool_display_name = generate_random_string(vcr_instance, cassette_name)
        sparkpool_full_path = cli_path_join(
            workspace.full_path, ".sparkpools", sparkpool_display_name + ".SparkPool"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {sparkpool_full_path} -P autoScale.minNodeCount=3"
        )

        # Assert
        upsert_spark_pool_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert sparkpool_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(sparkpool_full_path, query=".")
        assert (
            f'"name": "{sparkpool_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert '"nodeSize": "Small"' in mock_questionary_print.call_args[0][0]
        assert '"minNodeCount": 3' in mock_questionary_print.call_args[0][0]
        assert (
            '"maxNodeCount": 3' in mock_questionary_print.call_args[0][0]
        )  # maxNodeCount should be equal to minNodeCount

        # Cleanup
        rm(sparkpool_full_path)

    def test_mkdir_sparkpool_with_params_without_minNodeCount_success(
        self,
        workspace,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        sparkpool_display_name = generate_random_string(vcr_instance, cassette_name)
        sparkpool_full_path = cli_path_join(
            workspace.full_path, ".sparkpools", sparkpool_display_name + ".SparkPool"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {sparkpool_full_path} -P autoScale.maxNodeCount=3"
        )

        # Assert
        upsert_spark_pool_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert sparkpool_display_name in mock_print_done.call_args[0][0]

        mock_questionary_print.reset_mock()
        get(sparkpool_full_path, query=".")
        assert (
            f'"name": "{sparkpool_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert '"nodeSize": "Small"' in mock_questionary_print.call_args[0][0]
        assert '"minNodeCount": 1' in mock_questionary_print.call_args[0][0]
        assert (
            '"maxNodeCount": 3' in mock_questionary_print.call_args[0][0]
        )  # maxNodeCount should be equal to minNodeCount

        # Cleanup
        rm(sparkpool_full_path)

    def test_mkdir_sparkpool_name_already_exists_failure(
        self, virtual_item_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        sparkpool = virtual_item_factory(VirtualItemContainerType.SPARK_POOL)

        # Execute command
        cli_executor.exec_command(f"mkdir {sparkpool.full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_EXISTS)

    # region Capacity
    def test_mkdir_capacity_missing_az_values_failure(
        self, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        fab_default_az_subscription_id = state_config.get_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID
        )
        state_config.set_config(constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, "")
        capacity_display_name = "invalidcapacity"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

        # Cleanup
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, fab_default_az_subscription_id
        )

    def test_mkdir_capacity_without_params_failure(
        self, cli_executor, mock_questionary_print
    ):
        # Setup
        capacity_display_name = "capacityNoParams"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # We simulate -P without args when passing params=[]
        cli_executor.exec_command(f"mkdir {capacity_full_path} -P")

        # Assert
        no_params_message = "Params for '.Capacity'. Use key=value separated by commas."
        assert no_params_message in mock_questionary_print.call_args[0][0]

    def test_mkdir_capacity_missing_resource_group_failure(
        self, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        fab_default_az_subscription_id = state_config.get_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID
        )
        fab_default_az_resource_group = state_config.get_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP
        )
        state_config.set_config(constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, "")
        capacity_display_name = "invalidcapacity"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

        # Cleanup
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, fab_default_az_subscription_id
        )
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, fab_default_az_resource_group
        )

    def test_mkdir_capacity_missing_location_failure(
        self, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        fab_default_az_subscription_id = state_config.get_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID
        )
        fab_default_az_resource_group = state_config.get_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP
        )
        fab_default_az_location = state_config.get_config(
            constant.FAB_DEFAULT_AZ_LOCATION
        )
        state_config.set_config(constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_LOCATION, "")
        capacity_display_name = "invalidcapacity"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

        # Cleanup
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, fab_default_az_subscription_id
        )
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, fab_default_az_resource_group
        )
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_LOCATION, fab_default_az_location
        )

    def test_mkdir_capacity_missing_admin_failure(
        self, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        fab_default_az_subscription_id = state_config.get_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID
        )
        fab_default_az_resource_group = state_config.get_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP
        )
        fab_default_az_location = state_config.get_config(
            constant.FAB_DEFAULT_AZ_LOCATION
        )
        fab_default_az_admin = state_config.get_config(constant.FAB_DEFAULT_AZ_ADMIN)
        state_config.set_config(constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_LOCATION, "placeholder")
        state_config.set_config(constant.FAB_DEFAULT_AZ_ADMIN, "")
        capacity_display_name = "invalidcapacity"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

        # Cleanup
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_SUBSCRIPTION_ID, fab_default_az_subscription_id
        )
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_RESOURCE_GROUP, fab_default_az_resource_group
        )
        state_config.set_config(
            constant.FAB_DEFAULT_AZ_LOCATION, fab_default_az_location
        )
        state_config.set_config(constant.FAB_DEFAULT_AZ_ADMIN, fab_default_az_admin)

    def test_mkdir_capacity_with_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        setup_config_values_for_capacity,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        capacity_display_name = generate_random_string(vcr_instance, cassette_name)
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path} -P sku=F4")

        # Assert
        mock_print_done.assert_called_once()
        assert capacity_display_name in mock_print_done.call_args[0][0]

        get(capacity_full_path, query=".")
        assert (
            f'"name": "{capacity_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert test_data.admin.upn in mock_questionary_print.call_args[0][0]
        assert (
            f'"id": "/subscriptions/{test_data.azure_subscription_id}/resourceGroups/{test_data.azure_resource_group}/providers/Microsoft.Fabric/capacities/{capacity_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert f'"name": "F4"' in mock_questionary_print.call_args[0][0]
        # Cleanup
        rm(capacity_full_path)

    def test_mkdir_capacity_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        setup_config_values_for_capacity,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        # Setup
        capacity_display_name = generate_random_string(vcr_instance, cassette_name)
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert capacity_display_name in mock_print_done.call_args[0][0]

        get(capacity_full_path, query=".")
        assert (
            f'"name": "{capacity_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert test_data.admin.upn in mock_questionary_print.call_args[0][0]
        assert (
            f'"id": "/subscriptions/{test_data.azure_subscription_id}/resourceGroups/{test_data.azure_resource_group}/providers/Microsoft.Fabric/capacities/{capacity_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )

        # Cleanup
        rm(capacity_full_path)

    def test_mkdir_capacity_name_length_too_short_failure(
        self, cli_executor, assert_fabric_cli_error, setup_config_values_for_capacity
    ):
        # Setup
        capacity_display_name = "ca"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Name must be between 3 and 63 characters in length",
        )

    def test_mkdir_capacity_name_length_too_long_failure(
        self, cli_executor, assert_fabric_cli_error, setup_config_values_for_capacity
    ):
        # Setup
        capacity_display_name = "c" * 64
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Name must be between 3 and 63 characters in length",
        )

    def test_mkdir_capacity_name_invalid_pattern_failure(
        self, cli_executor, assert_fabric_cli_error, setup_config_values_for_capacity
    ):
        # Setup
        capacity_display_name = "CapaciTy"
        capacity_full_path = cli_path_join(
            ".capacities", capacity_display_name + ".Capacity"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {capacity_full_path}")

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Name must start with a lowercase letter and contain only lowercase letters or digits",
        )

    # endregion

    # region Domain
    def test_mkdir_domain_without_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_domain_to_cache,
    ):
        # Setup
        domain_display_name = generate_random_string(vcr_instance, cassette_name)
        domain_full_path = cli_path_join(".domains", domain_display_name + ".Domain")

        # Execute command
        cli_executor.exec_command(f"mkdir {domain_full_path}")

        # Assert
        upsert_domain_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert domain_display_name in mock_print_done.call_args[0][0]

        get(domain_full_path, query=".")
        assert domain_display_name in mock_questionary_print.call_args[0][0]
        assert "parentDomainId" not in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(domain_full_path)

    def test_mkdir_domain_with_params_success(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        upsert_domain_to_cache,
    ):
        # Setup
        parent_domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)
        get(parent_domain.full_path, query="id")
        parent_domain_id = mock_questionary_print.call_args[0][0]
        mock_print_done.reset_mock()
        upsert_domain_to_cache.reset_mock()
        domain_display_name = generate_random_string(vcr_instance, cassette_name)
        domain_full_path = cli_path_join(".domains", domain_display_name + ".Domain")

        # Execute command
        cli_executor.exec_command(
            f"mkdir {domain_full_path} -P description=test child domain,parentDomainName={parent_domain.display_name}.Domain"
        )

        # Assert
        upsert_domain_to_cache.assert_called_once()
        mock_print_done.assert_called_once()
        assert domain_display_name in mock_print_done.call_args[0][0]

        get(domain_full_path, query=".")
        assert domain_display_name in mock_questionary_print.call_args[0][0]
        assert (
            '"description": "test child domain"'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"parentDomainId": "{parent_domain_id}"'
            in mock_questionary_print.call_args[0][0]
        )

        # Cleanup
        rm(domain_full_path)

    def test_mkdir_domain_without_params_failure(
        self, cli_executor, mock_questionary_print
    ):

        domain_display_name = "domainNoParams"
        domain_full_path = cli_path_join(".domains", domain_display_name + ".Domain")

        # with params=[] we simulate -P without args
        cli_executor.exec_command(f"mkdir {domain_full_path} -P")

        no_params_message = "Params for '.Domain'. Use key=value separated by commas."
        assert no_params_message in mock_questionary_print.call_args[0][0]

    def test_mkdir_domain_name_already_exists_failure(
        self, cli_executor, assert_fabric_cli_error, virtual_workspace_item_factory
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Execute command
        cli_executor.exec_command(f"mkdir {domain.full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_ALREADY_EXISTS)

    # endregion

    # region ManagedIdentity
    def test_mkdir_managed_identity_success(
        self,
        workspace,
        cli_executor,
        mock_print_warning,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_managed_identity_to_cache,
        spy_provision_managed_identity,
    ):
        # Setup
        managed_identity_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        type = VirtualItemContainerType.MANAGED_IDENTITY
        managed_identity_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{managed_identity_display_name}.{str(VICMap[type])}",
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {managed_identity_full_path}")

        # Assert
        mock_print_warning.assert_called_once()
        mock_print_done.assert_called_once()
        upsert_managed_identity_to_cache.assert_called_once()
        # Managed Identity uses WS name as the name for newly created ManagedIdentity Item
        assert workspace.display_name in mock_print_done.call_args[0][0]
        spy_provision_managed_identity.assert_called_once()

        # Cleanup
        managed_identity_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{workspace.display_name}.{str(VICMap[type])}",
        )
        rm(managed_identity_full_path)

    # endregion

    # region ManagedPrivateEndpoint
    def test_mkdir_managed_private_endpoint_with_params_success(
        self,
        workspace,
        cli_executor,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_managed_private_endpoint_to_cache,
        spy_create_managed_private_endpoint,
        mock_questionary_print,
        test_data: StaticTestData,
    ):
        # Setup
        managed_private_endpoint_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        type = VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        managed_private_endpoint_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{managed_private_endpoint_display_name}.{str(VICMap[type])}",
        )
        subscription_id = test_data.azure_subscription_id
        resource_group = test_data.azure_resource_group
        sql_server = test_data.sql_server.server

        # Execute command
        cli_executor.exec_command(
            f"mkdir {managed_private_endpoint_full_path} -P targetPrivateLinkResourceId=/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server},targetSubresourceType=sqlServer"
        )

        # Assert
        spy_create_managed_private_endpoint.assert_called_once()
        mock_print_done.assert_called_once()
        upsert_managed_private_endpoint_to_cache.assert_called_once()
        assert managed_private_endpoint_display_name in mock_print_done.call_args[0][0]
        assert "created" in mock_print_done.call_args[0][0]

        # Sleep to wait for the gap between Azure and Fabric API
        # to be resolved. This is a workaround for the API gap.
        time.sleep(120)
        # Get the status from the managed private endpoint to check that it is approved
        get(managed_private_endpoint_full_path, query=".")
        assert '"status": "Pending"' in mock_questionary_print.call_args[0][0]

        # Cleanup
        rm(managed_private_endpoint_full_path)
        time.sleep(60)

    def test_mkdir_managed_private_endpoint_with_params_automatic_approval_success(
        self,
        workspace,
        cli_executor,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_managed_private_endpoint_to_cache,
        spy_create_managed_private_endpoint,
        mock_questionary_print,
        test_data: StaticTestData,
    ):
        # Setup
        managed_private_endpoint_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        type = VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        managed_private_endpoint_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{managed_private_endpoint_display_name}.{str(VICMap[type])}",
        )
        subscription_id = test_data.azure_subscription_id
        resource_group = test_data.azure_resource_group
        sql_server = test_data.sql_server.server

        # Execute command
        cli_executor.exec_command(
            f"mkdir {managed_private_endpoint_full_path} -P autoApproveEnabled=True,targetPrivateLinkResourceId=/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server},targetSubresourceType=sqlServer"
        )

        # Assert
        spy_create_managed_private_endpoint.assert_called_once()
        # Done is now created two times, once for the creation and once for the approval
        mock_print_done.assert_called()
        upsert_managed_private_endpoint_to_cache.assert_called_once()
        assert managed_private_endpoint_display_name in mock_print_done.call_args[0][0]
        assert "approved" in mock_print_done.call_args[0][0]

        # API GAP: We have to wait until the status is propagated to the Fabric API.
        time.sleep(200)

        # Get the status from the managed private endpoint to check that it is approved
        get(managed_private_endpoint_full_path, query=".")
        assert '"status": "Approved"' in mock_questionary_print.call_args[0][0]

        # Cleanup
        # Managed private endpoint could take a while to be provisioned - API GAP
        time.sleep(10)
        rm(managed_private_endpoint_full_path)
        time.sleep(60)

    def test_mkdir_managed_private_endpoint_without_params_fail(
        self,
        workspace,
        cli_executor,
        assert_fabric_cli_error,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_managed_private_endpoint_to_cache,
        spy_create_managed_private_endpoint,
    ):
        # Setup
        managed_private_endpoint_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        type = VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        managed_private_endpoint_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{managed_private_endpoint_display_name}.{str(VICMap[type])}",
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {managed_private_endpoint_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)
        mock_print_done.assert_not_called()
        upsert_managed_private_endpoint_to_cache.assert_not_called()
        spy_create_managed_private_endpoint.assert_not_called()

    def test_mkdir_managed_private_endpoint_forbidden_azure_access_pending_success(
        self,
        workspace,
        cli_executor,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_managed_private_endpoint_to_cache,
        spy_create_managed_private_endpoint,
        test_data: StaticTestData,
    ):
        """Test that when Azure access is forbidden during find_mpe_connection, the state is set to Pending."""
        # Setup
        managed_private_endpoint_display_name = generate_random_string(
            vcr_instance, cassette_name
        )
        type = VirtualItemContainerType.MANAGED_PRIVATE_ENDPOINT
        managed_private_endpoint_full_path = cli_path_join(
            workspace.full_path,
            str(type),
            f"{managed_private_endpoint_display_name}.{str(VICMap[type])}",
        )
        subscription_id = test_data.azure_subscription_id
        resource_group = test_data.azure_resource_group
        sql_server = test_data.sql_server.server

        with patch(
            "fabric_cli.utils.fab_cmd_mkdir_utils.find_mpe_connection"
        ) as mock_find_mpe:
            mock_find_mpe.side_effect = FabricCLIError(
                ErrorMessages.Common.forbidden(),
                constant.ERROR_FORBIDDEN,
            )

            # Execute command
            cli_executor.exec_command(
                f"mkdir {managed_private_endpoint_full_path} -P targetPrivateLinkResourceId=/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server},targetSubresourceType=sqlServer"
            )

            # Assert
            spy_create_managed_private_endpoint.assert_called_once()
            mock_print_done.assert_called_once()
            upsert_managed_private_endpoint_to_cache.assert_called_once()
            assert (
                f"'{managed_private_endpoint_display_name}.{str(VICMap[type])}' created. Private endpoint provisioning in Azure is pending approval"
                == mock_print_done.call_args[0][0]
            )

            # Verify that find_mpe_connection was called and threw the forbidden exception
            mock_find_mpe.assert_called_once()

        # Cleanup
        rm(managed_private_endpoint_full_path)

    # endregion

    # region ExternalDataShare
    def test_mkdir_external_data_share_with_params_success(
        self,
        workspace,
        item_factory,
        cli_executor,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_external_data_share_to_cache,
        spy_create_item_external_data_share,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        mock_print_done.reset_mock()
        eds_display_name = generate_random_string(vcr_instance, cassette_name)
        type = VirtualItemContainerType.EXTERNAL_DATA_SHARE
        eds_full_path = cli_path_join(
            workspace.full_path, str(type), f"{eds_display_name}.{str(VICMap[type])}"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {eds_full_path} -P paths=[Files/images/taxi_zone_map_bronx.jpg],recipient.userPrincipalName=lisa@fabrikam.com,recipient.tenantId=c51dc03f-268a-4da0-a879-25f24947ab8b,item={lakehouse.full_path}"
        )

        # Assert
        spy_create_item_external_data_share.assert_called_once()
        mock_print_done.assert_called_once()
        upsert_external_data_share_to_cache.assert_called_once()

        # Get eds_name from print:
        created_print = mock_print_done.call_args[0][0]
        match = re.search(r"'(.*?)'", created_print)
        if match:
            eds_long_name = match.group(1)
        else:
            raise Exception(
                "Unexpected error: could not find external data share name in print output"
            )
        parts = eds_long_name.split(".")

        generated_name = ".".join(parts[:2])
        eds_full_path = cli_path_join(
            workspace.full_path, str(type), f"{generated_name}.{str(VICMap[type])}"
        )

        # Cleanup
        rm(eds_full_path)

    def test_mkdir_external_data_share_without_params_fail(
        self,
        workspace,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_print_done,
        vcr_instance,
        cassette_name,
        upsert_external_data_share_to_cache,
        spy_create_item_external_data_share,
    ):
        # Setup
        eds_display_name = generate_random_string(vcr_instance, cassette_name)
        type = VirtualItemContainerType.EXTERNAL_DATA_SHARE
        eds_full_path = cli_path_join(
            workspace.full_path, str(type), f"{eds_display_name}.{str(VICMap[type])}"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {eds_full_path}")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)
        spy_create_item_external_data_share.assert_not_called()
        mock_print_done.assert_not_called()
        upsert_external_data_share_to_cache.assert_not_called()

    # endregion

    # region Connections
    def test_mkdir_connection_with_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):
        # Setup
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P connectionDetails.type=SQL,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert connection_display_name in mock_print_done.call_args[0][0]

        get(connection_full_path, query=".")
        assert (
            f'"displayName": "{connection_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert f'"type": "SQL"' in mock_questionary_print.call_args[0][0]
        assert (
            f'"connectivityType": "ShareableCloud"'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"path": "{test_data.sql_server.server}.database.windows.net;{test_data.sql_server.database}",'
            in mock_questionary_print.call_args[0][0]
        )

        # Cleanup
        rm(connection_full_path)

    def test_mkdir_connection_with_onpremises_gateway_params_success(
        self,
        cli_executor,
        mock_print_done,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):
        # Setup
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command with gateway and OnPremisesGateway connectivity type
        cli_executor.exec_command(
            f'mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values=\'[{{"gatewayId":"{test_data.onpremises_gateway_details.id}","encryptedCredentials":"{test_data.onpremises_gateway_details.encrypted_credentials}"}}]\''
        )

        # Assert
        mock_print_done.assert_called()
        assert mock_print_done.call_count == 1
        assert f"'{connection_display_name}.Connection' created\n" == mock_print_done.call_args[0][0]

        mock_print_done.reset_mock()
        
        # Cleanup
        rm(connection_full_path)

    def test_mkdir_connection_with_onpremises_gateway_params_ignore_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_print_warning,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):  
        # Setup
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values='[{{\"gatewayId\":\"{test_data.onpremises_gateway_details.id}\",\"encryptedCredentials\":\"{test_data.onpremises_gateway_details.encrypted_credentials}\",\"ignoreParameters\":\"ignoreParameters\"}}]'"
        )

        # Assert
        mock_print_done.assert_called()
        assert mock_print_done.call_count == 1
        assert f"'{connection_display_name}.Connection' created\n" == mock_print_done.call_args[0][0]

        mock_print_warning.assert_called()
        assert mock_print_warning.call_count == 1
        assert f"Ignoring unsupported parameters for on-premises gateway: ['ignoreparameters']" == mock_print_warning.call_args[0][0]

        # Cleanup
        rm(connection_full_path)


    def test_mkdir_connection_with_onpremises_gateway_params_failure(
        self,
        cli_executor,
        mock_fab_ui_print_error,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):
        # Setup
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Test 1: Execute command with missing values params
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic"
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert mock_fab_ui_print_error.call_count == 1
        assert mock_fab_ui_print_error.call_args[0][0].message == "Missing parameters for credential type Basic: ['values']"
        assert mock_fab_ui_print_error.call_args[0][0].status_code == "InvalidInput"

        mock_fab_ui_print_error.reset_mock()

        # Test 2: Execute command with missing encryptedCredentials params
        cli_executor.exec_command(
            f'mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values=\'[{{"gatewayId":"{test_data.onpremises_gateway_details.id}"}}]\''
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert mock_fab_ui_print_error.call_count == 1
        assert mock_fab_ui_print_error.call_args[0][0].message == ErrorMessages.Common.missing_onpremises_gateway_parameters(['encryptedCredentials'])
        assert mock_fab_ui_print_error.call_args[0][0].status_code == "InvalidInput"

        mock_fab_ui_print_error.reset_mock()

        # Test 3: Execute command with missing encryptedCredentials params in one of the values
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values='[{{\"gatewayId\":\"{test_data.onpremises_gateway_details.id}\",\"encryptedCredentials\":\"{test_data.onpremises_gateway_details.encrypted_credentials}\"}},{{\"encryptedCredentials\":\"{test_data.onpremises_gateway_details.encrypted_credentials}\"}}]'"
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert mock_fab_ui_print_error.call_count == 1
        assert mock_fab_ui_print_error.call_args[0][0].message == ErrorMessages.Common.missing_onpremises_gateway_parameters(['gatewayId'])
        assert mock_fab_ui_print_error.call_args[0][0].status_code == "InvalidInput"

        mock_fab_ui_print_error.reset_mock()

        # Test 4: Execute command with invalid json format for values
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values=[{{gatewayId:{test_data.onpremises_gateway_details.id}, encryptedCredentials:{test_data.onpremises_gateway_details.encrypted_credentials}}}]"
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert mock_fab_ui_print_error.call_count == 1
        assert mock_fab_ui_print_error.call_args[0][0].message == ErrorMessages.Common.invalid_onpremises_gateway_values()
        assert mock_fab_ui_print_error.call_args[0][0].status_code == "InvalidInput"

        mock_fab_ui_print_error.reset_mock()

        # Test 5: Execute command with invalid values as string array
        cli_executor.exec_command(
            f'mkdir {connection_full_path} -P gatewayId={test_data.onpremises_gateway_details.id},connectionDetails.type=SQL,connectivityType=OnPremisesGateway,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.values=\'["gatewayId", "encryptedCredentials"]\''
        )

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert mock_fab_ui_print_error.call_count == 1
        assert mock_fab_ui_print_error.call_args[0][0].message == ErrorMessages.Common.invalid_onpremises_gateway_values()
        assert mock_fab_ui_print_error.call_args[0][0].status_code == "InvalidInput"

    def test_mkdir_connection_with_gateway_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):
        # Setup
        gateway_display_name = generate_random_string(vcr_instance, cassette_name)
        gateway_full_path = cli_path_join(
            ".gateways", gateway_display_name + ".Gateway"
        )
        mkdir(
            gateway_full_path,
            params=[
                f"capacity={test_data.capacity.name},virtualNetworkName={test_data.vnet.name},subnetName={test_data.vnet.subnet}"
            ],
        )
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P gateway={gateway_display_name},connectionDetails.type=SQL,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
        )

        # Assert
        mock_print_done.assert_called()
        assert mock_print_done.call_count == 2
        assert connection_display_name in mock_print_done.call_args[0][0]

        get(connection_full_path, query=".")
        assert (
            f'"displayName": "{connection_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert f'"type": "SQL"' in mock_questionary_print.call_args[0][0]
        assert (
            f'"connectivityType": "VirtualNetworkGateway"'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"path": "{test_data.sql_server.server}.database.windows.net;{test_data.sql_server.database}",'
            in mock_questionary_print.call_args[0][0]
        )

        # Cleanup
        rm(connection_full_path)
        rm(gateway_full_path)

    def test_mkdir_connection_no_required_params_failure(
        self, cli_executor, mock_questionary_print
    ):
        # Setup
        connection_display_name = "connectionNoRequiredParams"
        capacity_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command
        # with params=[] we simulate -P without args
        cli_executor.exec_command(f"mkdir {capacity_full_path} -P")

        # Assert
        no_params_message = "Params for '.Connection'. Use key=value separated by commas.\n\nRequired params:\n  connectionDetails.parameters.*\n  connectionDetails.type\n  credentialDetails.*\n  credentialDetails.type"
        assert no_params_message in mock_questionary_print.call_args[0][0]

    def test_mkdir_connection_case_sensitivity_scenario_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command with mixed case parameters to test case sensitivity
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P connectionDetails.type=SQL,connectionDetails.parameters.Server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.Database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert connection_display_name in mock_print_done.call_args[0][0]

        # Cleanup
        rm(connection_full_path)

    def test_mkdir_connection_case_insensitive_parameter_matching_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        """Test that parameter name matching is case-insensitive for creation method inference."""
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command with lowercase parameter names (testing case insensitivity)
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P connectiondetails.type=SQL,connectiondetails.parameters.Server={test_data.sql_server.server}.database.windows.net,connectiondetails.parameters.database={test_data.sql_server.database},credentialdetails.type=Basic,credentialdetails.username={test_data.credential_details.username},credentialdetails.password={test_data.credential_details.password}"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert connection_display_name in mock_print_done.call_args[0][0]

        # Cleanup
        rm(connection_full_path)

    def test_mkdir_connection_no_matching_creation_method_case_sensitivity_failure(
        self, cli_executor, assert_fabric_cli_error
    ):
        """Test that no creation method is found when there's no parameter match, even with case differences."""
        connection_display_name = "connectionNoMatchingMethod"
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command with parameters that don't match any EventHub creation method
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P connectionDetails.type=EventHub,connectionDetails.parameters.server=test-server,connectionDetails.parameters.database=testdb,credentialDetails.type=Basic,credentialDetails.username=testuser,credentialDetails.password=testpass"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT,
            "Invalid creation method. Supported creation methods for EventHub are ['EventHub.Contents']",
        )

    def test_mkdir_connection_parameter_name_none_safety_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        """Test that parameter name None safety doesn't break normal operation."""
        connection_display_name = generate_random_string(vcr_instance, cassette_name)
        connection_full_path = cli_path_join(
            ".connections", connection_display_name + ".Connection"
        )

        # Execute command - this should work normally despite None safety checks
        cli_executor.exec_command(
            f"mkdir {connection_full_path} -P connectionDetails.type=SQL,connectionDetails.parameters.server={test_data.sql_server.server}.database.windows.net,connectionDetails.parameters.database={test_data.sql_server.database},credentialDetails.type=Basic,credentialDetails.username={test_data.credential_details.username},credentialDetails.password={test_data.credential_details.password}"
        )

        # Assert
        mock_print_done.assert_called_once()

        # Cleanup
        rm(connection_full_path)

    # endregion

    # region Gateways

    def test_mkdir_gateway_with_params_success(
        self,
        cli_executor,
        mock_print_done,
        mock_questionary_print,
        vcr_instance,
        test_data: StaticTestData,
        cassette_name,
    ):
        # Setup
        gateway_display_name = generate_random_string(vcr_instance, cassette_name)
        gateway_full_path = cli_path_join(
            ".gateways", gateway_display_name + ".Gateway"
        )

        # Execute command
        cli_executor.exec_command(
            f"mkdir {gateway_full_path} -P capacity={test_data.capacity.name},virtualNetworkName={test_data.vnet.name},subnetName={test_data.vnet.subnet}"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert gateway_display_name in mock_print_done.call_args[0][0]

        get(gateway_full_path, query=".")
        assert (
            f'"displayName": "{gateway_display_name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"inactivityMinutesBeforeSleep": 30'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"virtualNetworkName": "{test_data.vnet.name}"'
            in mock_questionary_print.call_args[0][0]
        )
        assert (
            f'"subnetName": "{test_data.vnet.subnet}"'
            in mock_questionary_print.call_args[0][0]
        )

        # Cleanup
        rm(gateway_full_path)

    def test_mkdir_getaways_no_required_params_failure(
        self, cli_executor, mock_questionary_print
    ):
        # Setup
        gateway_display_name = "getewaysNoRequiredParams"
        gateway_full_path = cli_path_join(
            ".gateways", gateway_display_name + ".Gateway"
        )

        # Execute command
        # with params=[] we simulate -P without args
        cli_executor.exec_command(f"mkdir {gateway_full_path} -P")

        no_params_message = "Params for '.Gateway'. Use key=value separated by commas.\n\nRequired params:\n  capacity|capacityId\n  subnetName\n  virtualNetworkName"
        assert no_params_message in mock_questionary_print.call_args[0][0]

    # endregion

    # region Output Tests
    def _verify_mkdir_workspace_output(
        self,
        cli_executor,
        workspace_display_name,
        capsys,
        output_format,
        test_data: StaticTestData,
    ):

        workspace_full_path = f"/{workspace_display_name}.Workspace"

        # Execute command
        cli_executor.exec_command(
            f"mkdir {workspace_full_path} -P capacityName={test_data.capacity.name} --output_format {output_format}"
        )

        # Get captured output
        captured = capsys.readouterr()

        # Verify exact stderr message
        assert captured.err.strip() == "Creating a new Workspace..."

        # Return captured output and path for specific format verification
        return captured, workspace_full_path

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Failed to run on windows since strip returns ' char in hexadecimal char and * is not returned",
    )
    def test_mkdir_workspace_verify_stderr_stdout_messages_text_format_success(
        self,
        cli_executor,
        capsys,
        vcr_instance,
        cassette_name,
        test_data: StaticTestData,
    ):
        workspace_display_name = generate_random_string(vcr_instance, cassette_name)
        captured, workspace_full_path = self._verify_mkdir_workspace_output(
            cli_executor,
            workspace_display_name,
            capsys,
            "text",
            test_data,
        )

        # Verify exact stdout message in text format
        assert f"* '{workspace_display_name}.Workspace' created" in captured.out.strip()

        # Cleanup
        rm(workspace_full_path)

    def test_mkdir_workspace_verify_stderr_stdout_messages_json_format_success(
        self,
        cli_executor,
        capsys,
        vcr_instance,
        cassette_name,
        mock_fab_set_state_config,
        test_data: StaticTestData,
    ):
        # Set output format to json
        mock_fab_set_state_config(constant.FAB_OUTPUT_FORMAT, "json")
        workspace_display_name = generate_random_string(vcr_instance, cassette_name)
        captured, workspace_full_path = self._verify_mkdir_workspace_output(
            cli_executor,
            workspace_display_name,
            capsys,
            "json",
            test_data,
        )

        # Verify exact stdout message in JSON format
        output = json.loads(captured.out)
        assert (
            output["result"]["message"]
            == f"'{workspace_display_name}.Workspace' created"
        )
        assert output["status"] == "Success"
        assert output["command"] == "mkdir"

        # Cleanup
        rm(workspace_full_path)

    # endregion

    # region Folders
    
    def test_mkdir_item_in_folder_listing_success(
        self, workspace, cli_executor, mock_print_done, mock_questionary_print, mock_fab_set_state_config, vcr_instance, cassette_name
    ):
        # Enable folder listing
        mock_fab_set_state_config(constant.FAB_FOLDER_LISTING_ENABLED, "true")

        
        # Setup
        folder_name = f"{generate_random_string(vcr_instance, cassette_name)}.Folder"
        folder_full_path = cli_path_join(workspace.full_path, folder_name)
        
        # Create folder
        cli_executor.exec_command(f"mkdir {folder_full_path}")
        mock_print_done.assert_called_once()
        mock_print_done.reset_mock()
        
        # Create notebook in folder
        notebook_name = f"{generate_random_string(vcr_instance, cassette_name)}.Notebook"
        notebook_full_path = cli_path_join(folder_full_path, notebook_name)
        cli_executor.exec_command(f"mkdir {notebook_full_path}")
        
        # Verify notebook appears in folder listing
        cli_executor.exec_command(f"ls {folder_full_path}")
        printed_output = mock_questionary_print.call_args[0][0]
        assert notebook_name in printed_output
        
        # Cleanup
        rm(notebook_full_path)
        rm(folder_full_path)


    def test_mkdir_folder_success(self, workspace, cli_executor, mock_print_done):
        # Setup
        folder_display_name = "folder"
        folder_full_path = cli_path_join(workspace.full_path, folder_display_name)

        # Execute command
        cli_executor.exec_command(f"mkdir {folder_full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert folder_display_name in mock_print_done.call_args[0][0]

        # Cleanup
        rm(folder_full_path)

    def test_mkdir_subfolder_success(
        self, vcr_instance, cassette_name, workspace, cli_executor, mock_print_done
    ):
        # Setup
        folder_name = f"{generate_random_string(vcr_instance, cassette_name)}.Folder"
        folder_full_path = cli_path_join(workspace.full_path, folder_name)
        subfolder_name = f"{generate_random_string(vcr_instance, cassette_name)}.Folder"
        subfolder_full_path = cli_path_join(folder_full_path, subfolder_name)

        # Execute command
        cli_executor.exec_command(f"mkdir {folder_full_path}")
        mock_print_done.assert_called_once()
        mock_print_done.reset_mock()
        cli_executor.exec_command(f"mkdir {subfolder_full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert subfolder_name in mock_print_done.call_args[0][0]

        # Cleanup
        rm(subfolder_full_path)
        rm(folder_full_path)

    def test_mkdir_folder_name_already_exists_failure(
        self, folder_factory, cli_executor, assert_fabric_cli_error
    ):
        # Setup
        folder = folder_factory()

        # Execute command
        cli_executor.exec_command(f"mkdir {folder.full_path}")

        assert_fabric_cli_error(constant.ERROR_ALREADY_EXISTS)

    # endregion

    # region Batch Output Tests
    def test_mkdir_single_item_creation_batch_output_structure_success(
        self, workspace, cli_executor, mock_print_done, mock_questionary_print, vcr_instance, cassette_name
    ):
        """Test that single item creation uses batched output structure."""
        # Setup
        lakehouse_display_name = generate_random_string(vcr_instance, cassette_name)
        lakehouse_full_path = cli_path_join(
            workspace.full_path, f"{lakehouse_display_name}.{ItemType.LAKEHOUSE}"
        )

        # Execute command
        cli_executor.exec_command(f"mkdir {lakehouse_full_path}")

        # Assert - verify output structure
        mock_print_done.assert_called_once()
        call_args = mock_print_done.call_args
        assert lakehouse_display_name in call_args[0][0]
        assert "created" in call_args[0][0]

        # Verify headers and values in mock_questionary_print.mock_calls
        # Look for the table output with headers
        output_calls = [str(call) for call in mock_questionary_print.mock_calls]
        table_output = "\n".join(output_calls)
        
        # Check for standard table headers
        assert "id" in table_output or "ID" in table_output
        assert "type" in table_output or "Type" in table_output
        assert "displayName" in table_output or "DisplayName" in table_output
        assert "workspaceId" in table_output or "WorkspaceId" in table_output
        
        # Check for actual values
        assert lakehouse_display_name in table_output
        assert "Lakehouse" in table_output

        # Cleanup
        rm(lakehouse_full_path)

    def test_mkdir_dependency_creation_batched_output_kql_database_success(
        self, workspace, cli_executor, mock_print_done, mock_questionary_print, vcr_instance, cassette_name
    ):
        """Test that KQL Database creation with EventHouse dependency produces batched output."""
        # Setup
        kqldatabase_display_name = generate_random_string(vcr_instance, cassette_name)
        kqldatabase_full_path = cli_path_join(
            workspace.full_path, f"{kqldatabase_display_name}.{ItemType.KQL_DATABASE}"
        )

        # Execute command (this will create EventHouse dependency automatically)
        cli_executor.exec_command(f"mkdir {kqldatabase_full_path}")

        # Assert - should have two print_done calls (one consolidated output with both items)
        # The current implementation may still have separate calls, but data should be collected
        assert mock_print_done.call_count >= 1

        
        # Verify both items are mentioned in output
        all_calls = [call.args[0] for call in mock_print_done.call_args_list]
        all_output = " ".join(all_calls)
        assert f"'{kqldatabase_display_name}_auto.{ItemType.EVENTHOUSE.value}' and '{kqldatabase_display_name}.{ItemType.KQL_DATABASE.value}' created" in all_output

        # Verify headers and values in mock_questionary_print.mock_calls for batched output
        output_calls = [str(call) for call in mock_questionary_print.mock_calls]
        table_output = "\n".join(output_calls)
        
        # Check for standard table headers (should appear once for consolidated table)
        assert "id" in table_output or "ID" in table_output
        assert "type" in table_output or "Type" in table_output
        assert "displayName" in table_output or "DisplayName" in table_output
        assert "workspaceId" in table_output or "WorkspaceId" in table_output
        
        # Check for both item values in the output
        assert kqldatabase_display_name in table_output
        assert f"{kqldatabase_display_name}_auto" in table_output  # EventHouse dependency name
        assert "KQLDatabase" in table_output or "KQL_DATABASE" in table_output
        assert "Eventhouse" in table_output or "EVENTHOUSE" in table_output

        # Cleanup - removing parent eventhouse removes the kqldatabase as well
        eventhouse_full_path = kqldatabase_full_path.removesuffix(".KQLDatabase") + "_auto.Eventhouse"
        rm(eventhouse_full_path)

    # endregion


# region Helper Methods
def mkdir(path, params=["run=true"]):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_mkdir_args(path, params)
    context = handle_context.get_command_context(args.path, False)
    fab_mkdir.exec_command(args, context)


def _build_mkdir_args(path, params):
    return argparse.Namespace(
        command="mkdir", command_path="mkdir", path=path, params=params
    )


def rm(path):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_rm_args(path)
    context = handle_context.get_command_context(args.path)
    fab_fs_rm.exec_command(args, context)


def _build_rm_args(path):
    return argparse.Namespace(command="rm", command_path="rm", path=path, force=True)


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


# region fixtures
@pytest.fixture()
def upsert_workspace_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_workspace_to_cache") as mock:
        yield mock


@pytest.fixture()
def upsert_domain_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_domain_to_cache") as mock:
        yield mock


@pytest.fixture()
def upsert_spark_pool_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_spark_pool_to_cache") as mock:
        yield mock


@pytest.fixture()
def upsert_item_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_item_to_cache") as mock:
        yield mock


@pytest.fixture()
def upsert_managed_identity_to_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.upsert_managed_identity_to_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def upsert_managed_private_endpoint_to_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.upsert_managed_private_endpoint_to_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def upsert_external_data_share_to_cache():
    with patch(
        "fabric_cli.utils.fab_mem_store.upsert_external_data_share_to_cache"
    ) as mock:
        yield mock


@pytest.fixture()
def spy_provision_managed_identity():
    with patch(
        "fabric_cli.client.fab_api_managedidentity.provision_managed_identity",
        side_effect=fab_api_managedidentity.provision_managed_identity,
    ) as mock:
        yield mock


@pytest.fixture()
def spy_create_managed_private_endpoint():
    with patch(
        "fabric_cli.client.fab_api_managedprivateendpoint.create_managed_private_endpoint",
        side_effect=fab_api_managedprivateendpoint.create_managed_private_endpoint,
    ) as mock:
        yield mock


@pytest.fixture()
def spy_create_item_external_data_share():
    with patch(
        "fabric_cli.client.fab_api_item.create_item_external_data_share",
        side_effect=fab_api_item.create_item_external_data_share,
    ) as mock:
        yield mock


# endregion
