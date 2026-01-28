# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import platform
from unittest.mock import ANY, patch

import pytest

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_types import ItemType


class TestExport:
    # region EXPORT
    @pytest.mark.parametrize("item_type,expected_file_extension", [
        (ItemType.NOTEBOOK, ".ipynb"),
        (ItemType.SPARK_JOB_DEFINITION, ".json"),
        (ItemType.DATA_PIPELINE, ".json"),
        (ItemType.MIRRORED_DATABASE, ".json")
    ])
    def test_export_item_success(
        self,
        item_factory,
        cli_executor,
        mock_print_done,
        tmp_path,
        mock_print_warning,
        item_type,
        expected_file_extension,
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {item.full_path} --output {str(tmp_path)} --force"
        )

        # Assert
        export_path = tmp_path / f"{item.display_name}.{item_type.value}"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == expected_file_extension for file in files)
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()
        mock_print_warning.assert_called_once()

    @pytest.mark.parametrize("item_type,expected_file_extension", [
        (ItemType.NOTEBOOK, ".ipynb"),
        (ItemType.SPARK_JOB_DEFINITION, ".json"),
        (ItemType.DATA_PIPELINE, ".json"),
        (ItemType.MIRRORED_DATABASE, ".json")
    ])
    def test_export_item_home_directory_path_success(
        self,
        item_factory,
        cli_executor,
        mock_print_done,
        tmp_path,
        monkeypatch,
        mock_print_warning,
        item_type,
        expected_file_extension,
    ):
        # Setup
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_dir_env = "USERPROFILE" if platform.system() == "Windows" else "HOME"
        monkeypatch.setenv(home_dir_env, str(home_dir))
        item = item_factory(item_type)
        output_dir = home_dir / "test_export"
        output_dir.mkdir()

        # Reset mock
        mock_print_done.reset_mock()
        mock_print_warning.reset_mock()

        # Execute command using ~/path notation
        cli_executor.exec_command(
            f"export {item.full_path} --output ~/test_export --force"
        )

        # Assert
        export_path = output_dir / f"{item.display_name}.{item_type.value}"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == expected_file_extension for file in files)
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()
        mock_print_warning.assert_called_once()

    @pytest.mark.parametrize("item_type", [
        ItemType.NOTEBOOK,
        ItemType.SPARK_JOB_DEFINITION,
        ItemType.DATA_PIPELINE,
        ItemType.MIRRORED_DATABASE,
        ItemType.REPORT,
        ItemType.SEMANTIC_MODEL,
        ItemType.KQL_DATABASE
    ])
    def test_export_item_invalid_output_path_failure(
        self, item_factory, cli_executor, mock_print_done, assert_fabric_cli_error, item_type
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {item.full_path} --output /invalid/path --force"
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
                call.args[0] == "2 items exported successfully\n"
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

    @pytest.mark.parametrize("item_type,export_format,expected_file_extension", [
        (ItemType.NOTEBOOK, ".py", ".py"),
        (ItemType.NOTEBOOK, ".ipynb", ".ipynb")
    ])
    def test_export_item_format_success(
        self, item_factory, cli_executor, mock_print_done, tmp_path, 
        item_type, export_format, expected_file_extension
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {item.full_path} --output {str(tmp_path)} --format {export_format} --force"
        )

        # Assert
        export_path = tmp_path / f"{item.display_name}.{item_type.value}"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == expected_file_extension for file in files)
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()

    @pytest.mark.parametrize("item_type,expected_file_count", [
        (ItemType.NOTEBOOK, 2),  # Default format for notebook is ipynb
        (ItemType.SPARK_JOB_DEFINITION, 2),
        (ItemType.DATA_PIPELINE, 2),
        (ItemType.MIRRORED_DATABASE, 2),
        (ItemType.REPORT, 4),
        (ItemType.SEMANTIC_MODEL, 3),
        (ItemType.KQL_DATABASE, 3),
    ])
    def test_export_item_default_format_success(
        self, item_factory, cli_executor, mock_print_done, tmp_path,
        item_type, expected_file_count
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command without format (should use default format from definition_format_mapping)
        cli_executor.exec_command(
            f"export {item.full_path} --output {str(tmp_path)} --force"
        )

        # Assert - should use default format for each item type
        export_path = tmp_path / f"{item.display_name}.{item_type.value}"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == expected_file_count
        assert any(file.name == ".platform" for file in files)
        mock_print_done.assert_called_once()

    @pytest.mark.parametrize("item_type,invalid_format,expected_error_suffix", [
        (ItemType.NOTEBOOK, ".txt", "Only the following formats are supported: .py, .ipynb"),
        (ItemType.SPARK_JOB_DEFINITION, ".txt", "No formats are supported"),
        (ItemType.DATA_PIPELINE, ".txt", "No formats are supported"),
        (ItemType.MIRRORED_DATABASE, ".txt", "No formats are supported")
    ])
    def test_export_item_invalid_format_failure(
        self,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        mock_print_done,
        tmp_path,
        item_type,
        invalid_format,
        expected_error_suffix,
    ):
        # Setup
        item = item_factory(item_type)

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"export {item.full_path} --output {str(tmp_path)} --format {invalid_format} --force"
        )

        # Assert
        assert_fabric_cli_error(constant.ERROR_INVALID_INPUT, f"Invalid format. {expected_error_suffix}")
        