# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import patch

import pytest

import fabric_cli.commands.fs.fab_fs_get as fab_get
import fabric_cli.commands.fs.fab_fs_ln as fab_ln
import fabric_cli.commands.fs.fab_fs_rm as fab_fs_rm
import fabric_cli.commands.fs.fab_fs_set as fab_set
import fabric_cli.core.fab_state_config as state_config
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import (
    ItemType,
    ITMutablePropMap,
    VirtualItemContainerType,
    VirtualWorkspaceType,
)
from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.processors import generate_random_string
from tests.test_commands.utils import cli_path_join


class TestSET:
    # region Item
    def test_set_item_invalid_query_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error, upsert_item_to_cache
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mocks
        upsert_item_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {lakehouse.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )
        upsert_item_to_cache.assert_not_called()

    @pytest.mark.parametrize("metadata_to_set", ["description", "displayName"])
    def test_set_item_metadata_success(
        self,
        item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_item_to_cache,
        metadata_to_set,
        vcr_instance,
        cassette_name,
    ):
        self._test_set_metadata_success(
            item_factory(ItemType.NOTEBOOK),
            mock_questionary_print,
            mock_print_done,
            upsert_item_to_cache,
            metadata_to_set,
            cli_executor,
            vcr_instance,
            cassette_name,
        )

    @pytest.mark.skip()
    def test_set_item_report_definition_semantic_model_id_success(
        self,
        item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_item_to_cache,
    ):
        # Setup
        report = item_factory(
            ItemType.REPORT, should_clean=False
        )  # will be cleaned up when semantic model is cleaned up
        new_semantic_model = item_factory(ItemType.SEMANTIC_MODEL)
        new_semantic_model_id = _get_id(
            new_semantic_model.full_path, mock_questionary_print
        )

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_item_to_cache.reset_mock()
        property_alias = "semanticModelId"

        # Execute command
        cli_executor.exec_command(
            f"set {report.full_path} --query {property_alias} --input {new_semantic_model_id} --force"
        )

        # Assert
        mock_print_done.assert_called_once()
        upsert_item_to_cache.assert_called_once()

        property_name = next(
            (
                kvp[property_alias]
                for kvp in ITMutablePropMap.get(ItemType.REPORT)
                if property_alias in kvp
            ),
            None,
        )
        get(report.full_path, query=property_name)
        assert mock_questionary_print.call_args[0][0] == new_semantic_model_id

    # endregion

    # region Workspace
    def test_set_workspace_invalid_query_failure(
        self,
        workspace,
        cli_executor,
        assert_fabric_cli_error,
        upsert_workspace_to_cache,
    ):
        # Execute command
        cli_executor.exec_command(
            f"set {workspace.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )
        upsert_workspace_to_cache.assert_not_called()

    @pytest.mark.parametrize("metadata_to_set", ["description", "displayName"])
    def test_set_workspace_metadata_success(
        self,
        workspace_factory,
        mock_questionary_print,
        mock_print_done,
        upsert_workspace_to_cache,
        metadata_to_set,
        cli_executor,
        vcr_instance,
        cassette_name,
    ):
        self._test_set_metadata_success(
            workspace_factory(),
            mock_questionary_print,
            mock_print_done,
            upsert_workspace_to_cache,
            metadata_to_set,
            cli_executor,
            vcr_instance,
            cassette_name,
        )

    @pytest.mark.parametrize(
        "query, input",
        [
            ("sparkSettings.automaticLog.enabled", "false"),
        ],
    )
    def test_set_workspace_success(
        self,
        query,
        input,
        workspace_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_workspace_to_cache,
    ):
        # Setup
        workspace = workspace_factory()

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_workspace_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {workspace.full_path} --query {query} --input {input} --force"
        )

        # Assert
        upsert_workspace_to_cache.assert_called_once()
        mock_print_done.assert_called_once()

        get(workspace.full_path, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

    # endregion

    # region SparkPool
    def test_set_sparkpool_invalid_query_failure(
        self,
        virtual_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        sparkpool = virtual_item_factory(VirtualItemContainerType.SPARK_POOL)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_spark_pool_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {sparkpool.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )
        upsert_spark_pool_to_cache.assert_not_called()

    @pytest.mark.parametrize(
        "query, input",
        [
            ("nodeSize", "Medium"),
            ("autoScale.enabled", "true"),
            ("autoScale.minNodeCount", "2"),
            ("autoScale.maxNodeCount", "5"),
        ],
    )
    def test_set_sparkpool_success(
        self,
        query,
        input,
        virtual_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_spark_pool_to_cache,
    ):
        # Setup
        # Setting maxNodeCount to 3 to be able to set minNodeCount to 2/3 since minNodeCount should be less than or equal to maxNodeCount
        sparkpool = virtual_item_factory(
            VirtualItemContainerType.SPARK_POOL, params=["autoScale.maxNodeCount=3"]
        )

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_spark_pool_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {sparkpool.full_path} --query {query} --input {input} --force"
        )

        # Assert
        upsert_spark_pool_to_cache.assert_called_once()
        mock_print_done.assert_called_once()

        get(sparkpool.full_path, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

    # endregion

    # region Capacity
    def test_set_capacity_invalid_query_failure(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
        setup_config_values_for_capacity,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {capacity.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )

    @pytest.mark.parametrize("query, input", [("sku.name", "F4")])
    def test_set_capacity_success(
        self,
        query,
        input,
        virtual_workspace_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        setup_config_values_for_capacity,
    ):
        # Setup
        capacity = virtual_workspace_item_factory(VirtualWorkspaceType.CAPACITY)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {capacity.full_path} --query {query} --input {input} --force"
        )

        # Assert
        mock_print_done.assert_called_once()

        get(capacity.full_path, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

    # endregion

    # region Domain
    def test_set_domain_invalid_query_failure(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {domain.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )

    @pytest.mark.parametrize("metadata_to_set", ["description", "displayName"])
    def test_set_domain_metadata_success(
        self,
        virtual_workspace_item_factory,
        mock_questionary_print,
        mock_print_done,
        upsert_domain_to_cache,
        metadata_to_set,
        cli_executor,
        vcr_instance,
        cassette_name,
    ):
        self._test_set_metadata_success(
            virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN),
            mock_questionary_print,
            mock_print_done,
            upsert_domain_to_cache,
            metadata_to_set,
            cli_executor,
            vcr_instance,
            cassette_name,
        )

    @pytest.mark.parametrize("query, input", [("contributorsScope", "AdminsOnly")])
    def test_set_domain_success(
        self,
        query,
        input,
        virtual_workspace_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_domain_to_cache,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_domain_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {domain.full_path} --query {query} --input {input} --force"
        )

        # Assert
        upsert_domain_to_cache.assert_called_once()
        mock_print_done.assert_called_once()

        get(domain.full_path, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

    # endregion

    # region Connection
    def test_set_connection_success(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        connection = virtual_workspace_item_factory(VirtualWorkspaceType.CONNECTION)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        input = generate_random_string(vcr_instance, cassette_name)
        query = "displayName"

        # Execute command
        cli_executor.exec_command(
            f"set {connection.full_path} --query {query} --input {input} --force"
        )

        full_path_new = connection.full_path.replace(connection.display_name, input)
        # Assert
        mock_print_done.assert_called_once()

        get(full_path_new, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

        # Clean up - update the full path of the renamed entities so the factory can clean them up
        set(full_path_new, query=query, input=connection.display_name)

    # endregion

    # region Gateway
    def test_set_gateway_virtualNetwork_success(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        gateway = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        query = "displayName"
        input = generate_random_string(vcr_instance, cassette_name)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {gateway.full_path} --query {query} --input {input} --force"
        )

        full_path_new = gateway.full_path.replace(gateway.display_name, input)
        # Assert
        mock_print_done.assert_called_once()

        get(full_path_new, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

        # Clean up - update the full path of the renamed entities so the factory can clean them up
        set(full_path_new, query=query, input=gateway.display_name)

    def test_set_gateway_duplicate_name_failure(
        self,
        virtual_workspace_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
    ):
        # Setup
        gateway1 = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)
        gateway2 = virtual_workspace_item_factory(VirtualWorkspaceType.GATEWAY)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {gateway1.full_path} --query displayName --input {gateway2.display_name} --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_DUPLICATE_GATEWAY_NAME,
            "The gateway DisplayName input is already being used by another gateway",
        )

    # endregion

    # region Shortcuts
    def test_set_shortcut_invalid_query_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)

        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "testShortcut.Shortcut"
        )
        target_path = cli_path_join(lakehouse2.full_path, "Files")
        ln(shortcut_path, target=target_path)

        shortcut = EntityMetadata(
            display_name="testShortcut",
            name="testShortcut.Shortcut",
            full_path=shortcut_path,
        )

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {shortcut.full_path} --query non_existent_query --input new_value --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_INPUT, "Invalid query 'non_existent_query'"
        )

    # endregion

    # region Folder

    @pytest.mark.parametrize("query, input", [("displayName", "randomFolder")])
    def test_set_folder_success(
        self,
        query,
        input,
        folder_factory,
        cli_executor,
        mock_questionary_print,
        mock_print_done,
        upsert_folder_to_cache,
    ):
        # Setup
        folder = folder_factory()

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        upsert_folder_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {folder.full_path} --query {query} --input {input} --force"
        )

        full_path_new = folder.full_path.replace(folder.display_name, input)
        # Assert
        upsert_folder_to_cache.assert_called_once()
        mock_print_done.assert_called_once()

        get(full_path_new, query=query)
        assert mock_questionary_print.call_args[0][0].lower() == input.lower()

        # Clean up - update the full path of the renamed entities so the factory can clean them up
        set(full_path_new, query=query, input=folder.display_name)

    # endregion

    # region Not Supported Entities
    def test_set_onelake_not_supported_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {lakehouse.full_path}/Files --query description --input 'new value' --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_virtual_item_not_supported_failure(
        self,
        virtual_item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_questionary_print,
        mock_print_done,
    ):
        # Setup
        virtual_item = virtual_item_factory(VirtualItemContainerType.MANAGED_IDENTITY)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {virtual_item.full_path} --query description --input 'new value' --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_UNSUPPORTED_COMMAND)

    # endregion

    def _test_set_metadata_success(
        self,
        entity: EntityMetadata,
        mock_questionary_print,
        mock_print_done,
        upsert_entity_to_cache,
        metadata_to_set,
        cli_executor,
        vcr_instance,
        cassette_name,
    ):
        # Setup
        new_metadata_value = generate_random_string(vcr_instance, cassette_name)

        # Reset mocks
        mock_questionary_print.reset_mock()
        mock_print_done.reset_mock()
        if upsert_entity_to_cache:
            upsert_entity_to_cache.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"set {entity.full_path} --query {metadata_to_set} --input {new_metadata_value} --force"
        )

        # Assert
        mock_print_done.assert_called_once()
        if upsert_entity_to_cache:
            upsert_entity_to_cache.assert_called_once()

        new_entity = entity

        if metadata_to_set == "displayName" or metadata_to_set == "name":
            new_entity = EntityMetadata(
                display_name=new_metadata_value,
                name=entity.name.replace(entity.display_name, new_metadata_value),
                full_path=entity.full_path.replace(
                    entity.display_name, new_metadata_value
                ),
            )

            with pytest.raises(FabricCLIError) as ex:
                get(entity.full_path)
            assert ex.value.status_code in (constant.ERROR_NOT_FOUND, "EntityNotFound")

        get(new_entity.full_path, query=metadata_to_set)
        assert mock_questionary_print.call_args[0][0] == new_metadata_value

        # Clean up - update the full path of the renamed entities so the factory can clean them up
        if metadata_to_set == "displayName":
            set(new_entity.full_path, query="displayName", input=entity.display_name)


# region Helper Methods
def set(path, query, input, force=True):
    state_config.set_config(constant.FAB_CACHE_ENABLED, "false")
    args = _build_set_args(path, query, input, force)
    context = handle_context.get_command_context(args.path)
    fab_set.exec_command(args, context)


def _build_set_args(path, query, input, force):
    return argparse.Namespace(
        command="set",
        command_path="set",
        path=path,
        query=query,
        input=input,
        force=force,
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
def upsert_folder_to_cache():
    with patch("fabric_cli.utils.fab_mem_store.upsert_folder_to_cache") as mock:
        yield mock


def _get_id(path, mock_questionary_print):
    get(path, query="id")
    return mock_questionary_print.call_args[0][0]


# endregion
