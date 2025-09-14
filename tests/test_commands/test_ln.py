# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse

import fabric_cli.commands.fs.fab_fs_get as fab_get
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.utils import cli_path_join


class TestLN:
    def test_ln_onelake_target_success(
        self,
        workspace,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)
        mock_print_done.reset_mock()

        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "testShortcut.Shortcut"
        )

        target_path = cli_path_join(lakehouse2.full_path, "Files")

        # Act
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --target {target_path} --force"
        )

        # Assert
        mock_print_done.assert_called_once()

    def test_ln_onelake_input_success(
        self,
        workspace,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)
        workspace_id = _get_id(workspace.full_path, mock_questionary_print)
        lakehouse_2_id = _get_id(lakehouse2.full_path, mock_questionary_print)
        mock_print_done.reset_mock()
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "testShortcut.Shortcut"
        )
        input = (
            "{"
            + f'"workspaceId":"{workspace_id}","itemId":"{lakehouse_2_id}","path":"Tables"'
            + "}"
        )

        # Act
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --force"
        )

        # Assert
        mock_print_done.assert_called_once()

    def test_ln_in_tablemaintenance_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "TableMaintenance", "shortcut.Short"
        )

        # Act
        input = "{}"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_PATH,
            constant.WARNING_ONLY_SUPPORTED_WITHIN_FILES_AND_TABLES,
        )

    def test_ln_in_warehouse_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        warehouse = item_factory(ItemType.WAREHOUSE)
        shortcut_path = cli_path_join(warehouse.full_path, "Files", "shortcut.Short")

        # Act
        input = "{}"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --force"
        )

        # Assert
        assert_fabric_cli_error(
            constant.ERROR_INVALID_PATH,
            constant.WARNING_ONLY_SUPPORTED_WITHIN_LAKEHOUSE,
        )

    def test_ln_no_shortcut_extension_in_path_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(lakehouse1.full_path, "Files", "shortcut.Short")

        # Act
        input = "{}"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_PATH)

    def test_ln_invalid_shortcut_name_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "shortcut<.Shortcut"
        )

        # Act
        input = "{}"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_PATH)

    def test_ln_input_and_target_specified_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "shortcut.Shortcut"
        )

        # Act
        target = "target"
        input = "{}"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type oneLake --input {input} --target {target} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_ln_input_and_target_not_specified_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "shortcut.Shortcut"
        )

        # Act
        cli_executor.exec_command(f"ln {shortcut_path} --type oneLake --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_ln_target_with_non_oneLake_type_failure(
        self, item_factory, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        shortcut_path = cli_path_join(
            lakehouse1.full_path, "Files", "shortcut.Shortcut"
        )

        # Act
        type = "amazonS3"
        target = "target"
        cli_executor.exec_command(
            f"ln {shortcut_path} --type {type} --target {target} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)


# region Helper Methods
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
    )


def _get_id(path, mock_questionary_print):
    get(path, query="id")
    return mock_questionary_print.call_args[0][0]


# endregion
