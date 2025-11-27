# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest

from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_context import Context
from fabric_cli.core.fab_types import ItemType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import Item, Tenant, Workspace


class TestCD:
    # region CD
    def test_cd_tenant_success(self, mock_print_done, cli_executor):
        # Execute command
        cli_executor.exec_command("cd /")

        # Assert
        mock_print_done.assert_called_once_with("Switched to root")
        assert isinstance(Context().context, Tenant)

    def test_cd_workspace_success(self, workspace, mock_print_done, cli_executor):
        # Execute command
        cli_executor.exec_command(f"cd {workspace.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Workspace)
        assert Context().context.name == workspace.name

    @pytest.mark.parametrize(
        "special_character",
        [
            " ",
            "&",
            "%",
            "$",
            "#",
            "@",
            "!",
            "^",
            "~",
            "(",
            ")",
            "-",
            "_",
            "+",
            "=",
            "{",
            "}",
            "[",
            "]",
            ";",
            # ":", need to fix tests in Windows
            "\\'",
            #'"', need to fix tests in Windows
            # "<", need to fix tests in Windows
            # ">", need to fix tests in Windows
            ",",
            ".",
            # "?", need to fix tests in Windows
            # "/", need to fix fab_handle_context to ignore valid names with /
        ],
    )
    def test_cd_workspace_with_special_characters_success(
        self,
        workspace_factory,
        mock_print_done,
        cli_executor,
        special_character,
    ):
        # Setup
        workspace = workspace_factory(special_character=special_character)
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(f"cd {workspace.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Workspace)
        assert Context().context.name == workspace.name.replace("\\'", "'")

    def test_cd_item_success(self, item_factory, mock_print_done, cli_executor):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        mock_print_done.reset_mock()

        #  Execute command
        cli_executor.exec_command(f"cd {lakehouse.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Item)
        assert Context().context.name == lakehouse.name

    def test_cd_folder_success(self, folder_factory, mock_print_done, cli_executor):
        # Setup
        folder = folder_factory()
        mock_print_done.reset_mock()

        #  Execute command
        cli_executor.exec_command(f"cd {folder.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Folder)
        assert Context().context.name == folder.name

    def test_cd_subfolder_success(self, folder_factory, mock_print_done, cli_executor):
        # Setup
        folder = folder_factory()
        subfolder = folder_factory(path=folder.full_path)
        nested_subfolder = folder_factory(path=subfolder.full_path)
        mock_print_done.reset_mock()

        #  Execute subfolder command
        cli_executor.exec_command(f"cd {subfolder.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Folder)
        assert Context().context.name == subfolder.name

        # Reset context
        mock_print_done.reset_mock()

        #  Execute nested_folder command
        cli_executor.exec_command(f"cd {nested_subfolder.full_path}")

        # Assert
        mock_print_done.assert_called_once()
        assert isinstance(Context().context, Folder)
        assert Context().context.name == nested_subfolder.name

    # endregion


@pytest.fixture(autouse=True)
def reset_context():
    yield
    # Reset context
    context = handle_context.get_command_context("/")
    Context().context = context
