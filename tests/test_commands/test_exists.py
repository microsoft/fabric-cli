# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.data.static_test_data import StaticTestData


class TestExists:
    # region EXISTS
    def test_exists_workspace_exists_success(
        self, workspace, mock_print_done, cli_executor
    ):
        # Execute command
        cli_executor.exec_command(f"exists {workspace.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert "true" in mock_print_done.call_args[0][0]

    def test_exists_item_exists_success(
        self, item_factory, mock_print_done, cli_executor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {lakehouse.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert "true" in mock_print_done.call_args[0][0]

    def test_exists_virtual_workspace_item_capacity_exists_success(
        self, mock_print_done, cli_executor, test_data: StaticTestData
    ):
        # Execute command
        cli_executor.exec_command(
            f"exists /.capacities/{test_data.capacity.name}.Capacity"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert "true" in mock_print_done.call_args[0][0]

    def test_exists_onelake_exists_success(
        self, item_factory, mock_print_done, cli_executor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {lakehouse.full_path}/Files")

        # Assert
        mock_print_done.assert_called_once()
        assert "true" in mock_print_done.call_args[0][0]

    def test_exists_item_doesnt_exist_success(
        self, item_factory, mock_print_done, cli_executor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        path = lakehouse.full_path.replace(".Lakehouse", "random.Lakehouse")
        cli_executor.exec_command(f"exists {path}")

        # Assert
        mock_print_done.assert_called_once()
        assert "false" in mock_print_done.call_args[0][0]

    def test_exists_onelake_doesnt_exist_success(
        self, item_factory, mock_print_done, cli_executor
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"exists {lakehouse.full_path}/Files/non_existent_file.txt"
        )

        # Assert
        mock_print_done.assert_called_once()
        assert "false" in mock_print_done.call_args[0][0]

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
        assert "true" in mock_print_done.call_args[0][0]

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
        assert "true" in mock_print_done.call_args[0][0]

    def test_exists_folder_doesnt_exist_success(
        self, workspace, mock_print_done, cli_executor
    ):
        # Setup

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"exists {workspace.full_path}/random_folder.Folder")

        # Assert
        mock_print_done.assert_called_once()
        assert "false" in mock_print_done.call_args[0][0]

    # endregion
