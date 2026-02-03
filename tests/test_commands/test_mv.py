# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from unittest.mock import patch
import pytest

import fabric_cli.commands.fs.fab_fs_ln as fab_ln
import fabric_cli.commands.fs.fab_fs_ls as fab_ls
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType, VirtualItemContainerType
from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.conftest import basic_item_parametrize, mkdir
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.utils import cli_path_join


class TestMV:
    def test_mv_workspace_to_workspace_non_recursive_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        mock_print_warning,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        notebook = item_factory(ItemType.NOTEBOOK, ws1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, ws1.full_path)
        f1 = folder_factory(path=ws1.full_path)  # Subfolder in f1
        sjd = item_factory(ItemType.SPARK_JOB_DEFINITION, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):

            mock_checkbox.return_value.ask.return_value = [
                notebook.name,
                data_pipeline.name,
            ]
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"mv {ws1.full_path} {ws2.full_path} --force")

            # Clean up - update the full path of the moved items so the factory can clean them up
            notebook.full_path = cli_path_join(ws2.full_path, notebook.name)
            data_pipeline.full_path = cli_path_join(
                ws2.full_path, data_pipeline.name)

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            assert any(
                call.args[0].startswith("2 items")
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                notebook.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert all(
                data_pipeline.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            # Assert that the subfolder was not copied
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Subfolder should not be copied when --recursive is not used"

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            # Assert that the subfolder was not copied
            assert not any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Subfolder should not be copied when --recursive is not used"
            assert not any(
                sjd.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Spark Job Definition should not be copied when --recursive is not used"

    def test_mv_workspace_to_workspace_recursive_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        mock_print_warning,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        # Create 2 items in ws1
        notebook = item_factory(ItemType.NOTEBOOK, ws1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, ws1.full_path)
        f1 = folder_factory(path=ws1.full_path)  # Subfolder in f1
        sjd = item_factory(ItemType.SPARK_JOB_DEFINITION, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        # TODO: Remove warning message from force delete
        mock_print_warning.reset_mock()

        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):

            mock_checkbox.return_value.ask.return_value = [
                notebook.name,
                data_pipeline.name,
                f1.name,
            ]
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"mv {ws1.full_path} {ws2.full_path} --force --recursive"
            )

            # Clean up - update the full path of the moved items so the factory can clean them up
            notebook.full_path = cli_path_join(ws2.full_path, notebook.name)
            data_pipeline.full_path = cli_path_join(
                ws2.full_path, data_pipeline.name)
            f1.full_path = cli_path_join(ws2.full_path, f1.name)
            sjd.full_path = cli_path_join(ws2.full_path, f1.name, sjd.name)

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called()
            assert any(
                call.args[0].startswith("2 items")
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                notebook.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert all(
                data_pipeline.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert all(
                f1.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f1.full_path)
            assert any(
                sjd.name in call.args[0] for call in mock_questionary_print.mock_calls
            )

    @pytest.mark.parametrize("item_type", [
        ItemType.DATA_PIPELINE, ItemType.KQL_DASHBOARD, ItemType.KQL_QUERYSET,
        ItemType.MIRRORED_DATABASE, ItemType.NOTEBOOK,
        ItemType.REFLEX, ItemType.SPARK_JOB_DEFINITION,
        ItemType.COSMOS_DB_DATABASE, ItemType.USER_DATA_FUNCTION,
    ])
    def test_mv_item_to_item_success(
        self,
        workspace_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        mock_print_warning,
        item_type,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        item = item_factory(item_type, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        with patch("questionary.confirm") as mock_confirm:

            mock_confirm.return_value.ask.return_value = True

            # Execute command
            target_path = cli_path_join(ws2.full_path, item.name)
            cli_executor.exec_command(
                f"mv {item.full_path} {target_path} --force")

            # Clean up - update the full path of the moved items so the factory can clean them up
            item.full_path = cli_path_join(ws2.full_path, item.name)

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                item.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                item.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    @pytest.mark.parametrize("unsupported_item_type", [
        ItemType.EVENTHOUSE,
        ItemType.KQL_DATABASE,
        ItemType.EVENTSTREAM,
    ])
    def test_mv_item_to_item_unsupported_failure(
        self,
        workspace_factory,
        item_factory,
        mock_print_done,
        assert_fabric_cli_error,
        mock_fab_ui_print_error,
        cli_executor: CLIExecutor,
        mock_print_warning,
        unsupported_item_type,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        item = item_factory(unsupported_item_type, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        with patch("questionary.confirm") as mock_confirm:

            mock_confirm.return_value.ask.return_value = True

            # Execute command
            target_path = cli_path_join(ws2.full_path, item.name)
            cli_executor.exec_command(
                f"mv {item.full_path} {target_path} --force")

            assert_fabric_cli_error(constant.ERROR_UNSUPPORTED_COMMAND)

    def test_mv_type_mismatch_error(
        self,
        workspace_factory,
        virtual_workspace_item_factory,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
    ):
        ws = workspace_factory()
        virtual_item = virtual_workspace_item_factory(
            VirtualWorkspaceType.CONNECTION)

        cli_executor.exec_command(
            f"mv {ws.full_path} {virtual_item.full_path} --force")

        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_mv_workspace_to_workspace_item_already_exists_success(
        self,
        workspace_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()

        notebook1 = item_factory(ItemType.NOTEBOOK, ws1.full_path)
        notebook2 = EntityMetadata(
            notebook1.display_name,
            notebook1.name,
            cli_path_join(ws2.full_path, notebook1.name),
        )
        mkdir(notebook2.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with (
            patch("questionary.checkbox") as mock_checkbox,
            patch("questionary.confirm") as mock_confirm,
        ):
            mock_checkbox.return_value.ask.return_value = [notebook1.name]
            mock_confirm.return_value.ask.return_value = True

            cli_executor.exec_command(
                f"mv {ws1.full_path} {ws2.full_path} --force")

            # Clean up - update the full path of the moved items so the factory can clean them up
            notebook1.full_path = cli_path_join(ws2.full_path, notebook1.name)

            # Assert
            mock_print_done.assert_called()
            assert any(
                "moved successfully" in call.args[0]
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                notebook1.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                notebook1.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_mv_item_from_workspace_to_workspace_when_item_already_exists(
        self,
        workspace_factory,
        cli_executor: CLIExecutor,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()

        notebook1 = item_factory(ItemType.NOTEBOOK, ws1.full_path)
        notebook2 = EntityMetadata(
            notebook1.display_name,
            notebook1.name,
            cli_path_join(ws2.full_path, notebook1.name),
        )
        mkdir(notebook2.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            # Execute command
            target_path = cli_path_join(ws2.full_path, notebook1.name)
            cli_executor.exec_command(
                f"mv {notebook1.full_path} {target_path} --force")

            # Clean up - update the full path of the moved items so the factory can clean them up
            notebook1.full_path = cli_path_join(ws2.full_path, notebook1.name)

            # Assert
            mock_print_done.assert_called()
            assert any(
                call.args[0] == "Move completed\n" for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                notebook1.display_name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                notebook1.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_mv_from_empty_workspace_failure(
        self,
        workspace_factory,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
        mock_print_done,
        mock_questionary_print,
        mock_fab_logger_log_warning,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            # Execute command
            cli_executor.exec_command(f"mv {ws1.full_path} {ws2.full_path}")

            # Assert
            assert_fabric_cli_error(constant.ERROR_INVALID_OPERATION)

    def test_mv_item_workspace_to_workspace_no_confirmation_failure(
        self,
        workspace_factory,
        cli_executor: CLIExecutor,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        mock_fab_ui_print_error,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()

        # Create item in ws1
        notebook1 = item_factory(ItemType.NOTEBOOK, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False

            target_path = cli_path_join(ws2.full_path, notebook1.name)

            # Execute command
            cli_executor.exec_command(
                f"mv {notebook1.full_path} {target_path}")

        # assert
        assert mock_questionary_print.call_count == 0
        assert mock_print_done.call_count == 0
        assert mock_confirm.call_count == 1

    def test_mv_workspace_to_workspace_empty_failure(
        self, workspace, cli_executor: CLIExecutor, assert_fabric_cli_error
    ):
        target_path = "My workspace.Personal"

        # Execute command
        cli_executor.exec_command(
            f"mv {workspace.full_path} {target_path} --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_OPERATION)

    def test_mv_workspace_to_item_type_mismatch_failure(
        self,
        workspace,
        item_factory,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)

        # Execute command
        cli_executor.exec_command(
            f"mv {workspace.full_path} {notebook.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    @pytest.mark.parametrize("source_type,target_type", [
        (ItemType.NOTEBOOK, ItemType.DATA_PIPELINE),
        (ItemType.REPORT, ItemType.LAKEHOUSE),
        (ItemType.SEMANTIC_MODEL, ItemType.WAREHOUSE)
    ])
    def test_mv_item_to_item_type_mismatch_failure(
        self,
        item_factory,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
        source_type,
        target_type,
    ):
        # Setup
        source_item = item_factory(source_type)
        target_item = item_factory(target_type)

        cli_executor.exec_command(
            f"mv {source_item.full_path} {target_item.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    @pytest.mark.parametrize("item_type", [
        ItemType.DATA_PIPELINE, ItemType.KQL_DASHBOARD, ItemType.KQL_QUERYSET,
        ItemType.MIRRORED_DATABASE, ItemType.NOTEBOOK,
        ItemType.REFLEX, ItemType.SPARK_JOB_DEFINITION,
        ItemType.COSMOS_DB_DATABASE, ItemType.USER_DATA_FUNCTION,
    ])
    def test_mv_item_within_workspace_rename_success(
        self,
        workspace_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        item_type,
    ):
        # Setup
        ws1 = workspace_factory()
        # Create item in ws1
        item = item_factory(item_type, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            renamed_item_name = f"{item.display_name} Renamed.{item_type}"

            # Execute command
            target_path = cli_path_join(ws1.full_path, renamed_item_name)
            cli_executor.exec_command(
                f"mv {item.full_path} {target_path} --force")

            # Clean up - update the full path of the moved items so the factory can clean them up
            item.full_path = target_path

            # Assert
            mock_print_done.assert_called()
            assert any(
                call.args[0] == "Move completed\n" for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                item.name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                renamed_item_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_mv_item_within_workspace_failure(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        cli_executor: CLIExecutor,
        assert_fabric_cli_error,
        mock_print_done,
        mock_questionary_print,
    ):
        # Setup
        ws1 = workspace_factory()
        # Create folder in ws1
        folder = folder_factory(path=ws1.full_path)
        # Create item in ws1
        notebook = item_factory(ItemType.NOTEBOOK, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            target_path = cli_path_join(folder.full_path, notebook.name)
            cli_executor.exec_command(
                f"mv {notebook.full_path} {target_path} --force")

            # Assert
            assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_mv_folder_to_workspace_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)
        # Create 2 items in f1
        notebook = item_factory(ItemType.NOTEBOOK, f1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()
        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"mv {f1.full_path} {ws2.full_path} --force --recursive"
            )

            # Clean up - update the full path of the moved items so the factory can clean them up
            notebook.full_path = cli_path_join(ws2.full_path, notebook.name)
            data_pipeline.full_path = cli_path_join(
                ws2.full_path, data_pipeline.name)
            f1.full_path = cli_path_join(ws2.full_path, f1.name)

            # Assert
            mock_print_done.assert_called()
            # TODO: Fix output message for cp and mv commands
            # assert any(
            #     call.args[0].startswith("2 items")
            #     for call in mock_print_done.mock_calls
            # )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert all(
                f1.name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f1.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_mv_folder_inside_workspace_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
        vcr_instance,
        cassette_name,
    ):
        ws = workspace_factory()

        # Create source folder and destination folder
        dest_folder = folder_factory(path=ws.full_path)
        source_folder = folder_factory(path=ws.full_path)

        # Create items in the source folder
        notebook = item_factory(ItemType.NOTEBOOK, source_folder.full_path)
        data_pipeline = item_factory(
            ItemType.DATA_PIPELINE, source_folder.full_path)

        # Create a nested folder inside source folder
        nested_folder = folder_factory(path=source_folder.full_path)
        nested_item = item_factory(
            ItemType.SPARK_JOB_DEFINITION, nested_folder.full_path
        )

        # Reset mock
        mock_print_done.reset_mock()
        mock_questionary_print.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Execute command - move source folder inside destination folder
            cli_executor.exec_command(
                f"mv {source_folder.full_path} {dest_folder.full_path} --force --recursive"
            )

            # Clean up - update the full paths of the moved items so the factory can clean them up
            moved_source_folder_path = cli_path_join(
                dest_folder.full_path, source_folder.name
            )
            notebook.full_path = cli_path_join(
                moved_source_folder_path, notebook.name)
            data_pipeline.full_path = cli_path_join(
                moved_source_folder_path, data_pipeline.name
            )
            nested_folder.full_path = cli_path_join(
                moved_source_folder_path, nested_folder.name
            )
            nested_item.full_path = cli_path_join(
                nested_folder.full_path, nested_item.name
            )
            source_folder.full_path = moved_source_folder_path

            # Assert that the move completed successfully
            mock_print_done.assert_called()

            # Verify source folder is no longer in its original location
            mock_questionary_print.reset_mock()
            ls(ws.full_path)
            # Should see destination folder but not source folder at workspace root
            assert any(
                dest_folder.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            # Source folder should not be at workspace root anymore
            source_folder_at_root = any(
                source_folder.name in call.args[0]
                and dest_folder.name not in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert (
                not source_folder_at_root
            ), "Source folder should not be at workspace root anymore"

            # Verify source folder is now inside destination folder
            mock_questionary_print.reset_mock()
            ls(dest_folder.full_path)
            assert any(
                source_folder.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            # Verify items are preserved inside the moved folder
            mock_questionary_print.reset_mock()
            ls(moved_source_folder_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                nested_folder.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            # Verify nested items are preserved
            mock_questionary_print.reset_mock()
            ls(nested_folder.full_path)
            assert any(
                nested_item.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )


# region Helper Methods
def ls(path, long=False, all=False, query=None):
    args = _build_ls_args(path, long, all, query)
    context = handle_context.get_command_context(args.path)
    fab_ls.exec_command(args, context)


def _build_ls_args(path, long, all, query):
    return argparse.Namespace(
        command="ls", command_path="ls", path=path, long=long, all=all, query=query
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
