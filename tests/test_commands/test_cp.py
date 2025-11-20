# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import os
import shutil
import tempfile
from unittest.mock import patch

import fabric_cli.commands.fs.fab_fs_cp as fab_cp
import fabric_cli.commands.fs.fab_fs_ls as fab_ls
from fabric_cli.core import fab_constant
from fabric_cli.core import fab_constant as constant
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_types import ItemType, VirtualWorkspaceType
from fabric_cli.core.hiearchy.fab_folder import Folder
from fabric_cli.core.hiearchy.fab_hiearchy import LocalPath, OneLakeItem
from fabric_cli.errors import ErrorMessages
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.conftest import rm
from tests.test_commands.data.models import EntityMetadata
from tests.test_commands.utils import cli_path_join


class TestCP:
    def test_cp_workspace_to_workspace_non_recursive_success(
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
        notebook = item_factory(ItemType.NOTEBOOK, path=ws1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, path=ws1.full_path)
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
            cli_executor.exec_command(f"cp {ws1.full_path} {ws2.full_path} --force")

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            assert any(
                call.args[0]
                == f"2 items copied successfully from {ws1.full_path} to {ws2.full_path}"
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
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
            # Assert that the subfolder was not copied
            assert not any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Subfolder should not be copied when --recursive is not used"
            assert not any(
                sjd.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Spark Job Definition should not be copied when --recursive is not used"

    def test_cp_workspace_to_workspace_recursive_success(
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
        notebook = item_factory(ItemType.NOTEBOOK, path=ws1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, path=ws1.full_path)
        f1 = folder_factory(path=ws1.full_path)  # Subfolder in f1
        sjd = item_factory(ItemType.SPARK_JOB_DEFINITION, path=f1.full_path)
        f2 = folder_factory(path=f1.full_path)  # Subfolder in f2
        notebook2 = item_factory(ItemType.NOTEBOOK, path=f2.full_path)
        f3 = folder_factory(path=f2.full_path)  # Subfolder in f3
        data_pipeline2 = item_factory(ItemType.DATA_PIPELINE, path=f3.full_path)

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
                f1.name,
            ]
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {ws1.full_path} {ws2.full_path} --force --recursive"
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            assert any(
                call.args[0]
                == f"2 items and 1 folders copied successfully from {ws1.full_path} to {ws2.full_path}"
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
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
            assert any(
                f2.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f2.full_path)
            assert any(
                notebook2.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                f3.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f3.full_path)
            assert any(
                data_pipeline2.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_cp_workspace_to_folder_success(
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
        f2 = folder_factory(path=ws2.full_path)
        # Create 2 items in ws1
        notebook = item_factory(ItemType.NOTEBOOK, path=ws1.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, path=ws1.full_path)

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
            cli_executor.exec_command(f"cp {ws1.full_path} {f2.full_path} --force")

            copied_notebook = EntityMetadata(
                notebook.display_name,
                notebook.name,
                cli_path_join(f2.full_path, notebook.name),
            )

            copied_eventhouse = EntityMetadata(
                data_pipeline.display_name,
                data_pipeline.name,
                cli_path_join(f2.full_path, data_pipeline.name),
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            assert any(
                call.args[0]
                == f"2 items copied successfully from {ws1.full_path} to {f2.full_path}"
                for call in mock_print_done.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                f2.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f2.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                data_pipeline.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            rm(copied_notebook.full_path)
            rm(copied_eventhouse.full_path)

    def test_cp_item_to_item_success(
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
        notebook = item_factory(ItemType.NOTEBOOK, ws1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with patch("questionary.confirm") as mock_confirm:

            mock_confirm.return_value.ask.return_value = True

            # Execute command
            to_path = cli_path_join(ws2.full_path, notebook.display_name + ".Notebook")
            cli_executor.exec_command(f"cp {notebook.full_path} {to_path}")

            # Assert
            mock_print_done.assert_called()

            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                notebook.display_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )

    def test_cp_workspace_to_workspace_type_mismatch_failure(
        self, workspace, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Setup
        to_path = "My workspace.Personal"

        # Execute command
        cli_executor.exec_command(f"cp {workspace.full_path} {to_path} --force")

    #     # Assert
    #     assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_cp_workspace_to_item_type_mismatch_failure(
        self,
        workspace,
        item_factory,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)

        # Execute command
        cli_executor.exec_command(
            f"cp {workspace.full_path} {notebook.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT)

    def test_cp_item_to_item_type_mismatch_failure(
        self, item_factory, assert_fabric_cli_error, cli_executor: CLIExecutor
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        eventhouse = item_factory(ItemType.EVENTHOUSE)

        # Execute command
        cli_executor.exec_command(
            f"cp {eventhouse.full_path} {notebook.full_path} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_UNSUPPORTED_COMMAND)

    def test_cp_virtual_workspace_item_domain_not_supported_failure(
        self,
        virtual_workspace_item_factory,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        domain = virtual_workspace_item_factory(VirtualWorkspaceType.DOMAIN)

        # Execute command
        cli_executor.exec_command(f"cp {domain.full_path} {domain.full_path} --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_UNSUPPORTED_COMMAND)

    def test_cp_onelake_to_onelake_success(
        self,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)
        # Upload local file to lakehouse1
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_name = "test_cp_ol2ol.txt"
            file_path = cli_path_join(tmp_dir, file_name)
            with open(file_path, "wb") as fp:
                fp.write(b"Hello world!\n")

            lakehouse1_onelake_full_path = cli_path_join(
                lakehouse1.full_path, "Files", file_name
            )
            lakehouse2_onelake_full_path = cli_path_join(lakehouse2.full_path, "Files")

            # Reset mock
            mock_print_done.reset_mock()

            with patch("questionary.confirm") as mock_confirm:

                mock_confirm.return_value.ask.return_value = True

                # Upload local file to lakehouse1
                _upload_local_file_to_onelake(file_path, lakehouse1_onelake_full_path)
                # Delete the temporary file
                os.remove(file_path)

                # Execute command
                cli_executor.exec_command(
                    f"cp {lakehouse1_onelake_full_path} {lakehouse2_onelake_full_path}"
                )
                # Assert
                mock_print_done.assert_called()
                mock_questionary_print.reset_mock()
                ls(lakehouse2_onelake_full_path)
                assert any(
                    file_name in call.args[0]
                    for call in mock_questionary_print.mock_calls
                )

                # Execute command on renamed file
                renamed_file_name = "renamed_" + file_name
                lakehouse2_onelake_full_path_rn = cli_path_join(
                    lakehouse2.full_path, "Files", renamed_file_name
                )
                cli_executor.exec_command(
                    f"cp {lakehouse1_onelake_full_path} {lakehouse2_onelake_full_path_rn}"
                )
                # Assert
                mock_print_done.assert_called()
                mock_questionary_print.reset_mock()
                ls(lakehouse2_onelake_full_path)
                assert any(
                    renamed_file_name in call.args[0]
                    for call in mock_questionary_print.mock_calls
                )

    def test_cp_from_onelake_recursive_unsupported(
        self,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse1 = item_factory(ItemType.LAKEHOUSE)
        lakehouse2 = item_factory(ItemType.LAKEHOUSE)
        lakehouse1_onelake_full_path = cli_path_join(lakehouse1.full_path, "Files")
        lakehouse2_onelake_full_path = cli_path_join(lakehouse2.full_path, "Files")

        # Reset mock
        mock_print_done.reset_mock()

        with patch("questionary.confirm") as mock_confirm:

            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {lakehouse1_onelake_full_path} {lakehouse2_onelake_full_path}"
            )

            # Assert
            assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    def test_cp_local_to_onelake_success(
        self,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        lakehouse_onelake_full_path = cli_path_join(lakehouse.full_path, "Files")

        # Reset mock
        mock_print_done.reset_mock()

        with patch("questionary.confirm") as mock_confirm:

            mock_confirm.return_value.ask.return_value = True

            with tempfile.TemporaryDirectory() as tmp_dir:
                file_name = "test_cp_lo2ol.txt"
                file_path = cli_path_join(tmp_dir, file_name)
                with open(file_path, "wb") as fp:
                    fp.write(b"Hello world!\n")

                # Execute command
                cli_executor.exec_command(
                    f"cp {file_path} {lakehouse_onelake_full_path}"
                )

                # Assert
                mock_print_done.assert_called()
                mock_questionary_print.reset_mock()
                ls(lakehouse_onelake_full_path)
                # Extract the file name from the path
                assert any(
                    file_name in call.args[0]
                    for call in mock_questionary_print.mock_calls
                )

                # Execute command on renamed file
                renamed_file_name = "renamed_" + file_name
                lakehouse_onelake_full_path_rn = cli_path_join(
                    lakehouse.full_path, "Files", renamed_file_name
                )
                cli_executor.exec_command(
                    f"cp {file_path} {lakehouse_onelake_full_path_rn}"
                )
                # Assert
                mock_print_done.assert_called()
                mock_questionary_print.reset_mock()
                ls(lakehouse_onelake_full_path)
                assert any(
                    renamed_file_name in call.args[0]
                    for call in mock_questionary_print.mock_calls
                )

                # Delete the temporary file
                os.remove(file_path)

    def test_cp_from_local_recursive_unsupported(
        self,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        lakehouse_onelake_full_path = cli_path_join(lakehouse.full_path, "Files")
        td = tempfile.TemporaryDirectory()

        # Reset mock
        mock_print_done.reset_mock()

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(f"cp {td.name} {lakehouse_onelake_full_path}")

            # Assert
            assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

        shutil.rmtree(td.name, ignore_errors=True)

    def test_cp_onelake_to_local_success(
        self,
        item_factory,
        mock_print_done,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        lakehouse_onelake_full_path = cli_path_join(lakehouse.full_path, "Files")
        with tempfile.TemporaryDirectory() as td:
            file_name = "test_cp_ol2lo.txt"
            file_path = cli_path_join(td, file_name)
            with open(file_path, "wb") as fp:
                fp.write(b"Hello world!\n")

            # Upload local file to lakehouse
            _upload_local_file_to_onelake(file_path, lakehouse_onelake_full_path)

            with patch("questionary.confirm") as mock_confirm:
                mock_confirm.return_value.ask.return_value = True

                source_file_path = cli_path_join(lakehouse_onelake_full_path, file_name)

                # Reset mock
                mock_print_done.reset_mock()

                # Execute command
                cli_executor.exec_command(f"cp {source_file_path} {td}")

                # Assert
                mock_print_done.assert_called()
                # Check that the file exists in the temporary directory
                assert os.path.exists(cli_path_join(td, file_name))

                # Execute command on renamed file
                renamed_file_name = "renamed_" + file_name
                dest_file_path_rn = cli_path_join(td, renamed_file_name)

                # Reset mock
                mock_print_done.reset_mock()

                # Execute command
                cli_executor.exec_command(f"cp {source_file_path} {dest_file_path_rn}")

                # Assert
                mock_print_done.assert_called()
                assert os.path.exists(dest_file_path_rn)

    def test_cp_onelake_to_local_parquet_binary_success(
        self,
        item_factory,
        mock_print_done,
        cli_executor: CLIExecutor,
    ):
        """Test copying a parquet file (binary format) from OneLake to local preserves binary content."""
        # Setup
        lakehouse = item_factory(ItemType.LAKEHOUSE)
        lakehouse_onelake_full_path = cli_path_join(lakehouse.full_path, "Files")

        with tempfile.TemporaryDirectory() as td:
            # Generate parquet file on the fly instead of using hard-coded test data
            file_name = "test.parquet"
            file_path = cli_path_join(td, file_name)
            _generate_test_binary_file(file_path)

            _upload_local_file_to_onelake(file_path, lakehouse_onelake_full_path)

            with patch("questionary.confirm") as mock_confirm:
                mock_confirm.return_value.ask.return_value = True

                source_file_path = cli_path_join(lakehouse_onelake_full_path, file_name)

                # Reset mock
                mock_print_done.reset_mock()

                # Execute command to download the parquet file
                downloaded_file_path = cli_path_join(td, "downloaded_" + file_name)
                cli_executor.exec_command(
                    f"cp {source_file_path} {downloaded_file_path}"
                )

                # Assert that the command completed successfully
                mock_print_done.assert_called()
                assert os.path.exists(downloaded_file_path)

                # Most importantly: verify that the binary content is preserved exactly
                with open(downloaded_file_path, "rb") as fp:
                    original_content = fp.read()

                with open(downloaded_file_path, "rb") as fp:
                    downloaded_content = fp.read()

                assert (
                    downloaded_content == original_content
                ), "Parquet file binary content was corrupted during download"
                assert len(downloaded_content) == len(
                    original_content
                ), "File size changed during download"

    def test_cp_folder_to_workspace_non_recursive_failure(
        self,
        workspace_factory,
        folder_factory,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)

        cli_executor.exec_command(f"cp {f1.full_path} {ws2.full_path} --force")

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_OPERATION)

    def test_cp_folder_to_workspace_sucess(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)

        # Create an item in the folder
        notebook = item_factory(ItemType.NOTEBOOK, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {f1.full_path} {ws2.full_path} --force --recursive"
            )

            f2 = EntityMetadata(
                f1.display_name, f1.name, cli_path_join(ws2.full_path, f1.name)
            )
            notebook2 = EntityMetadata(
                notebook.display_name,
                notebook.name,
                cli_path_join(f2.full_path, notebook.name),
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            mock_questionary_print.reset_mock()
            # Inside the workspace there is the source folder
            ls(ws2.full_path)
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_print_done.assert_called()
            mock_questionary_print.reset_mock()
            # Inside the copied folder there is the item
            ls(f2.full_path)
            assert any(
                notebook2.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            rm(notebook2.full_path)
            rm(f2.full_path)

    def test_cp_folder_to_workspace_nested_folder_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)
        sf1 = folder_factory(path=f1.full_path)  # Subfolder in f1
        f2 = folder_factory(
            path=ws2.full_path, should_clean=False
        )  # Prevent cleaning the folder to avoid error, workspace delete will clean it

        # Create an item in the folder
        notebook = item_factory(ItemType.NOTEBOOK, path=f1.full_path)
        sjd = item_factory(ItemType.SPARK_JOB_DEFINITION, path=sf1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {f1.full_path} {f2.full_path} --force --recursive"
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                f2.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(f2.full_path)
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(cli_path_join(f2.full_path, f1.name))
            assert any(
                notebook.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            )
            assert any(
                sf1.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Subfolder should be copied to the destination folder"
            mock_questionary_print.reset_mock()
            ls(cli_path_join(f2.full_path, f1.name, sf1.name))
            assert any(
                sjd.name in call.args[0] for call in mock_questionary_print.mock_calls
            ), "Spark Job Definition should be copied to the newly created subfolder"

    def test_cp_folder_to_existing_folder_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)
        f2 = folder_factory(path=ws2.full_path)

        # Create an item in the folder
        notebook = item_factory(ItemType.NOTEBOOK, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {f1.full_path} {f2.full_path} --force --recursive"
            )

            copied_f1 = EntityMetadata(
                f1.display_name, f1.name, cli_path_join(f2.full_path, f1.name)
            )
            copied_notebook = EntityMetadata(
                notebook.display_name,
                notebook.name,
                cli_path_join(copied_f1.full_path, notebook.name),
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            mock_questionary_print.reset_mock()
            ls(f2.full_path)
            assert any(
                f1.name in call.args[0] for call in mock_questionary_print.mock_calls
            )
            mock_questionary_print.reset_mock()
            ls(copied_f1.full_path)
            assert any(
                notebook.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            ), "Notebook should be copied to the newly created folder"

            rm(copied_notebook.full_path)
            rm(copied_f1.full_path)

    def test_cp_folder_to_non_existing_folder_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)

        # Create an item in the folder
        notebook = item_factory(ItemType.NOTEBOOK, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {f1.full_path} {ws2.full_path}/NewFolder.Folder --force --recursive"
            )

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            mock_questionary_print.reset_mock()
            ls(ws2.full_path)
            assert any(
                "NewFolder.Folder" in call.args[0]
                for call in mock_questionary_print.mock_calls
            ), "New folder should be created in the destination workspace"
            mock_questionary_print.reset_mock()
            ls(cli_path_join(ws2.full_path, "NewFolder.Folder"))
            assert any(
                notebook.name in call.args[0]
                for call in mock_questionary_print.mock_calls
            ), "Notebook should be copied to the newly created folder"

    def test_cp_folder_to_same_workspace_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        # Setup
        ws1 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)

        # Create an item in the folder
        notebook = item_factory(ItemType.NOTEBOOK, path=f1.full_path)

        # Reset mock
        mock_print_done.reset_mock()

        with (patch("questionary.confirm") as mock_confirm,):
            mock_confirm.return_value.ask.return_value = True

            # Execute command
            cli_executor.exec_command(
                f"cp {f1.full_path} {ws1.full_path} --force --recursive"
            )

            new_folder_name = f"{(f1.name.split('.')[0])}_copy.Folder"
            new_notebook_name = f"{(notebook.name.split('.')[0])}_copy.Notebook"

            # Assert
            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            mock_questionary_print.reset_mock()
            ls(ws1.full_path)
            assert any(
                new_folder_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            ), "New folder should be created in the same workspace with '_copy' suffix"
            mock_questionary_print.reset_mock()
            ls(cli_path_join(ws1.full_path, new_folder_name))
            assert any(
                new_notebook_name in call.args[0]
                for call in mock_questionary_print.mock_calls
            ), "Notebook should be copied to the newly created folder with '_copy' suffix"

    def _setup_name_conflict_scenario(
        self, workspace_factory, folder_factory, item_factory
    ):
        ws1 = workspace_factory()
        ws2 = workspace_factory()
        f1 = folder_factory(path=ws1.full_path)
        f2 = folder_factory(path=ws2.full_path)

        source_notebook = item_factory(ItemType.NOTEBOOK, path=ws1.full_path)

        existing_notebook = item_factory(
            ItemType.NOTEBOOK,
            path=f2.full_path,
            custom_name=source_notebook.display_name,
        )

        return ws1, ws2, f1, f2, source_notebook, existing_notebook

    def _reset_mocks_and_setup_confirm(self, mock_print_done, mock_print_warning):
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()
        return patch("questionary.confirm")

    def test_cp_item_existing_name_different_location_without_block_on_path_collision_success(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        mock_print_warning,
        mock_questionary_print,
        cli_executor: CLIExecutor,
    ):
        ws1, ws2, f1, f2, source_notebook, existing_notebook = (
            self._setup_name_conflict_scenario(
                workspace_factory, folder_factory, item_factory
            )
        )

        with self._reset_mocks_and_setup_confirm(
            mock_print_done, mock_print_warning
        ) as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            cli_executor.exec_command(
                f"cp {source_notebook.full_path} {ws2.full_path}/{source_notebook.name} --force"
            )

            mock_print_warning.assert_called()
            mock_print_done.assert_called()

            assert any(
                "Copy completed" in str(call) for call in mock_print_done.mock_calls
            )

    def test_cp_item_existing_name_different_location_with_block_on_path_collision_failure(
        self,
        workspace_factory,
        folder_factory,
        item_factory,
        mock_print_done,
        assert_fabric_cli_error,
        cli_executor: CLIExecutor,
    ):
        ws1, ws2, f1, f2, source_notebook, existing_notebook = (
            self._setup_name_conflict_scenario(
                workspace_factory, folder_factory, item_factory
            )
        )

        cli_executor.exec_command(
            f"cp {source_notebook.full_path} {ws2.full_path}/{source_notebook.name} --force --block_on_path_collision"
        )

        assert_fabric_cli_error(
            fab_constant.ERROR_INVALID_INPUT,
            ErrorMessages.Cp.item_exists_different_path(),
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


def _upload_local_file_to_onelake(local_file_path: str, onelake_path: str):
    from_ctxt = handle_context.get_command_context(
        local_file_path, supports_local_path=True
    )
    assert isinstance(from_ctxt, LocalPath)
    to_ctxt = handle_context.get_command_context(onelake_path, raise_error=False)
    assert isinstance(to_ctxt, OneLakeItem)

    args = argparse.Namespace(
        command="cp",
        command_path="cp",
        from_path=[local_file_path],
        to_path=[onelake_path],
        force=True,
    )
    fab_cp.exec_command(args, from_ctxt, to_ctxt)


def _generate_test_binary_file(file_path: str):
    """
    Generate a simple binary file for testing copy operations.
    Creates a file with various binary patterns to test binary integrity.
    """
    with open(file_path, "wb") as f:
        # Simple binary patterns to test copy integrity
        f.write(b"TESTFILE")  # Text header
        f.write(bytes(range(256)))  # All byte values 0-255
        f.write(b"\x00" * 100)  # Null bytes
        f.write(b"\xff" * 100)  # All 1s
        f.write(b"ENDTEST")  # Text footer


# endregion
