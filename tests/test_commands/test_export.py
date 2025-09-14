# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import platform
from unittest.mock import ANY, patch

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_types import ItemType


class TestExport:
    # region EXPORT
    def test_export_item_success(
        self,
        item_factory,
        cli_executor,
        mock_print_done,
        tmp_path,
        mock_print_warning,
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(tmp_path)} --force"
        )

        # Assert
        export_path = tmp_path / f"{notebook.display_name}.Notebook"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == ".ipynb" for file in files)
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()
        mock_print_warning.assert_called_once()

    def test_export_item_home_directory_path_success(
        self,
        item_factory,
        cli_executor,
        mock_print_done,
        tmp_path,
        monkeypatch,
        mock_print_warning,
    ):
        # Setup
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_dir_env = "USERPROFILE" if platform.system() == "Windows" else "HOME"
        monkeypatch.setenv(home_dir_env, str(home_dir))
        notebook = item_factory(ItemType.NOTEBOOK)
        output_dir = home_dir / "test_export"
        output_dir.mkdir()

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command using ~/path notation
        cli_executor.exec_command(
            f"export {notebook.full_path} --output ~/test_export --force"
        )

        # Assert
        export_path = output_dir / f"{notebook.display_name}.Notebook"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == ".ipynb" for file in files)
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()
        mock_print_warning.assert_called_once()

    def test_export_item_invalid_output_path_failure(
        self, item_factory, cli_executor, mock_print_done, assert_fabric_cli_error
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {notebook.full_path} --output /invalid/path --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_PATH)

    def test_export_workspace_success(
        self,
        item_factory,
        cli_executor,
        workspace,
        mock_print_done,
        tmp_path,
        mock_print_warning,
    ):
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)  # item has a definition
        spark_job_definition = item_factory(
            ItemType.SPARK_JOB_DEFINITION
        )  # item has a definition
        # item does not have a definition
        ml_model = item_factory(ItemType.ML_MODEL)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = [
                notebook.display_name + ".Notebook",
                spark_job_definition.display_name + ".SparkJobDefinition",
            ]

            # Execute command
            cli_executor.exec_command(
                f"export {workspace.full_path} --output {str(tmp_path)} --force"
            )

            # Assert ml_model was not an option as does not have definition
            _, call_kwargs = mock_checkbox.call_args
            assert call_kwargs["choices"] == [
                notebook.display_name + ".Notebook",
                spark_job_definition.display_name + ".SparkJobDefinition",
            ]

            mock_print_done.assert_called()
            mock_print_warning.assert_called_once()
            assert any(
                call.args[0] == "2 items exported successfully"
                for call in mock_print_done.mock_calls
            )

            # Assert notebook
            notebook_export_path = tmp_path / f"{notebook.display_name}.Notebook"
            assert notebook_export_path.is_dir()
            files = list(notebook_export_path.iterdir())
            assert len(files) == 2
            assert any(file.suffix == ".ipynb" for file in files)
            assert any(file.name == ".platform" for file in files)

            # Assert spark job definition
            sjd_export_path = (
                tmp_path / f"{spark_job_definition.display_name}.SparkJobDefinition"
            )
            assert sjd_export_path.is_dir()
            files = list(sjd_export_path.iterdir())
            assert len(files) == 2
            assert any(file.suffix == ".json" for file in files)
            assert any(file.name == ".platform" for file in files)

    def test_export_workspace_empty_failure(
        self, workspace, cli_executor, assert_fabric_cli_error, tmp_path
    ):
        # Execute command
        cli_executor.exec_command(
            f"export {workspace.full_path} --output {str(tmp_path)} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_OPERATION)

    def test_export_workspace_with_no_items_supporting_export_failure(
        self, item_factory, cli_executor, assert_fabric_cli_error, workspace, tmp_path
    ):
        # Setup
        _ = item_factory(ItemType.ML_MODEL)  # item does not have a definition

        # Execute command
        cli_executor.exec_command(
            f"export {workspace.full_path} --output {str(tmp_path)} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_NOT_SUPPORTED)

    # endregion
