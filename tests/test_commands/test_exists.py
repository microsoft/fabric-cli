# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.data.static_test_data import StaticTestData
from tests.test_commands.conftest import item_type_paramerter, exists_onelake_parameters


class TestExists:
    # region EXISTS
    def test_exists_workspace_exists_success(
        self, workspace, mock_print_done, cli_executor
    ):
        # Execute command
        cli_executor.exec_command(f"exists {workspace.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    @item_type_paramerter
    def test_exists_item_exists_success(
        self, item_factory, mock_print_done, cli_executor, item_type
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {item.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    def test_exists_virtual_workspace_item_capacity_exists_success(
        self, mock_print_done, cli_executor, test_data: StaticTestData
    ):
        # Execute command
        cli_executor.exec_command(
            f"exists /.capacities/{test_data.capacity.name}.Capacity"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    @exists_onelake_parameters
    def test_exists_onelake_exists_success(
        self, item_factory, mock_print_done, cli_executor, item_type, folder_name, created_by_default
    ):
        # Skip combinations where folder is not created by default
        if not created_by_default:
            pytest.skip(
                f"{folder_name} folder not created by default for {item_type}")

        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {item.full_path}/{folder_name}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    @item_type_paramerter
    def test_exists_item_doesnt_exist_success(
        self, item_factory, mock_print_done, cli_executor, item_type
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        item_extension = f".{item_type.value}"
        path = item.full_path.replace(
            item_extension, f"random{item_extension}")
        cli_executor.exec_command(f"exists {path}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_FALSE in mock_print_done.call_args[0][0]

    @exists_onelake_parameters
    def test_exists_onelake_doesnt_exist_success(
        self, item_factory, mock_print_done, cli_executor, item_type, folder_name, created_by_default
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"exists {item.full_path}/{folder_name}/non_existent_file.txt"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_FALSE in mock_print_done.call_args[0][0]

    def test_exists_folder_exists_success(
        self, folder_factory, mock_print_done, cli_executor
    ):
        # Setup
        folder = folder_factory()

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {folder.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    def test_exists_subfolder_exists_success(
        self, folder_factory, mock_print_done, cli_executor
    ):
        # Setup
        folder = folder_factory()
        subfolder = folder_factory(path=folder.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {subfolder.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_TRUE in mock_print_done.call_args[0][0]

    def test_exists_folder_doesnt_exist_success(
        self, workspace, mock_print_done, cli_executor
    ):
        # Setup

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"exists {workspace.full_path}/random_folder.Folder")

        # Assert
        mock_print_done.assert_called_once()
        assert constant.INFO_EXISTS_FALSE in mock_print_done.call_args[0][0]

    # endregion
