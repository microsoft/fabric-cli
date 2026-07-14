# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

from fabric_cli.core import fab_constant as constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from fabric_cli.errors.bulk_export import BulkExportErrors


class TestBulkExport:

    def test_bulk_export_item_fail(
        self, item_factory, cli_executor, assert_fabric_cli_error, tmp_path
    ):
        # Setup
        item = item_factory(ItemType.NOTEBOOK)

        # Execute command - bulk-export is not supported on individual items
        cli_executor.exec_command(
            f"bulk-export {item.full_path} --output {str(tmp_path)} --force --recursive"
        )

        # Assert - should fail with error indicating invalid target
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.invalid_target(item.name),
        )

    def test_bulk_export_workspace_folder_without_recursive_fail(
        self,
        folder_factory,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        tmp_path,
    ):
        # Setup
        folder = folder_factory()
        _ = item_factory(ItemType.NOTEBOOK, path=folder.full_path)

        # Execute command with --preserve_binding but without --recursive (which is required for workspace/folder)
        cli_executor.exec_command(
            f"bulk-export {folder.full_path} --output {str(tmp_path)} --force"
        )

        # Assert - should fail with error indicating recursive is required
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.recursive_flag_required(),
        )

    def test_bulk_export_workspace_without_recursive_fail(
        self, workspace, item_factory, cli_executor, assert_fabric_cli_error, tmp_path
    ):
        # Setup
        _ = item_factory(ItemType.NOTEBOOK, path=workspace.full_path)

        # Execute command with --preserve_binding but without --recursive (which is required for workspace)
        cli_executor.exec_command(
            f"bulk-export {workspace.full_path} --output {str(tmp_path)} --force"
        )

        # Assert - should fail with error indicating recursive is required
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.recursive_flag_required(),
        )

    def test_bulk_export_empty_folder_fail(
        self, cli_executor, folder_factory, assert_fabric_cli_error, tmp_path
    ):
        # Setup
        folder = folder_factory()

        # Execute command with --recursive on empty folder
        cli_executor.exec_command(
            f"bulk-export {folder.full_path} --output {str(tmp_path)} --force --recursive"
        )

        # Assert - should fail with error indicating target is empty
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.empty_target(folder.name),
        )

    def test_bulk_export_empty_workspace_fail(
        self, cli_executor, workspace, assert_fabric_cli_error, tmp_path
    ):
        # Execute command with --recursive on empty workspace
        cli_executor.exec_command(
            f"bulk-export {workspace.full_path} --output {str(tmp_path)} --force --recursive"
        )

        # Assert - should fail with error indicating target is empty
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.empty_target(workspace.name),
        )

    def test_bulk_export_no_exportable_items_fail(
        self,
        folder_factory,
        item_factory,
        cli_executor,
        assert_fabric_cli_error,
        tmp_path,
    ):
        # Setup - create a folder with unsupported items only
        folder = folder_factory()
        _ = item_factory(ItemType.ENVIRONMENT, path=folder.full_path)

        # Execute command with --recursive on folder with no exportable items
        with patch(
            "fabric_cli.utils.fab_cmd_bulk_export_utils.is_command_supported"
        ) as side_effect_mock:
            # Mock is_command_supported to return False for ENVIRONMENT item to simulate unsupported item type
            def is_command_supported_side_effect(element):
                if element.item_type == ItemType.ENVIRONMENT:
                    raise FabricCLIError()
                return True

            side_effect_mock.side_effect = is_command_supported_side_effect
            cli_executor.exec_command(
                f"bulk-export {folder.full_path} --output {str(tmp_path)} --force --recursive"
            )

        # Assert - should fail with error indicating no exportable items
        assert_fabric_cli_error(
            constant.ERROR_INVALID_OPERATION,
            BulkExportErrors.no_exportable_items(),
        )

    def test_bulk_export_output_path_not_empty_warning(
        self, workspace, item_factory, cli_executor, mock_print_warning, tmp_path
    ):
        # Setup - create a notebook and an existing file in the output path
        _ = item_factory(ItemType.NOTEBOOK, path=workspace.full_path)
        existing_file = tmp_path / "existing_file.txt"
        existing_file.touch()

        # Execute command with --force to bypass confirmation but should still print warning about non-empty output path
        cli_executor.exec_command(
            f"bulk-export {workspace.full_path} --output {str(tmp_path)} --force --recursive"
        )

        # Assert - should print warning about non-empty output path
        mock_print_warning.assert_called_with("Exporting to a non-empty output folder")

    def test_bulk_export_inner_folder_structure_success(
        self,
        folder_factory,
        item_factory,
        cli_executor,
        tmp_path,
        mock_print_warning,
    ):
        # Setup - create workspace/folder/item structure
        folder1 = folder_factory()
        folder2 = folder_factory(path=folder1.full_path)
        _ = item_factory(ItemType.NOTEBOOK, path=folder1.full_path)
        notebook2 = item_factory(ItemType.NOTEBOOK, path=folder2.full_path)

        with patch("fabric_cli.utils.fab_ui.print_output_format") as mock_print_output:
            # Execute bulk-export on top-level folder with --recursive
            cli_executor.exec_command(
                f"bulk-export {folder2.full_path} --output {str(tmp_path)} --recursive --force"
            )

            # Assert - should print warning about sensitivity labels and confirm export completion
            mock_print_warning.assert_called_once_with(
                "Item definitions are exported without their sensitivity labels"
            )
            mock_print_output.assert_called_once()
            call_kwargs = mock_print_output.call_args
            assert "Exported 1 items" in call_kwargs.kwargs.get(
                "message", call_kwargs[1].get("message", "")
            )

        # Assert
        export_path = (
            tmp_path / folder2.display_name / f"{notebook2.display_name}.Notebook"
        )
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == ".py" for file in files)
        assert any(file.name == ".platform" for file in files)

    def test_bulk_export_workspace_with_folders_structure_success(
        self,
        folder_factory,
        item_factory,
        cli_executor,
        workspace,
        tmp_path,
        mock_print_warning,
    ):
        # Setup
        folder1 = folder_factory(path=workspace.full_path)
        folder2 = folder_factory(path=folder1.full_path)
        notebook1 = item_factory(ItemType.NOTEBOOK, path=folder1.full_path)
        notebook2 = item_factory(ItemType.NOTEBOOK, path=folder2.full_path)

        # Reset mock
        mock_print_warning.reset_mock()

        with patch("fabric_cli.utils.fab_ui.print_output_format") as mock_print_output:
            # Execute command
            cli_executor.exec_command(
                f"bulk-export {workspace.full_path} --output {str(tmp_path)} --force --recursive"
            )

            # Assert
            export_path1 = (
                tmp_path / folder1.display_name / f"{notebook1.display_name}.Notebook"
            )
            export_path2 = (
                tmp_path
                / folder1.display_name
                / folder2.display_name
                / f"{notebook2.display_name}.Notebook"
            )
            assert export_path1.is_dir()
            assert export_path2.is_dir()
            files1 = list(export_path1.iterdir())
            files2 = list(export_path2.iterdir())
            assert len(files1) == 2
            assert len(files2) == 2
            assert any(file.suffix == ".py" for file in files1)
            assert any(file.suffix == ".py" for file in files2)
            assert any(file.name == ".platform" for file in files1)
            assert any(file.name == ".platform" for file in files2)
            mock_print_output.assert_called_once()
            call_kwargs = mock_print_output.call_args
            message = call_kwargs.kwargs.get(
                "message", call_kwargs[1].get("message", "")
            )
            assert "Exported 2 items" in message
            assert "Skipped" not in message
            mock_print_warning.assert_called_once()

    def test_bulk_export_workspace_with_unsupported_items_success(
        self,
        cli_executor,
        workspace,
        item_factory,
        tmp_path,
    ):
        # unsupported items are items that are not supported by the bulk-export command, but user has required permissions
        # Setup - create a workspace with both supported and unsupported items
        notebook = item_factory(ItemType.NOTEBOOK, path=workspace.full_path)
        _ = item_factory(ItemType.ENVIRONMENT, path=workspace.full_path)

        with patch("fabric_cli.utils.fab_ui.print_output_format") as mock_print_output:
            # Execute command
            with patch(
                "fabric_cli.utils.fab_cmd_bulk_export_utils.is_command_supported"
            ) as side_effect_mock:
                # Mock is_command_supported to return False for ENVIRONMENT item to simulate unsupported item type
                def is_command_supported_side_effect(element):
                    if element.item_type == ItemType.ENVIRONMENT:
                        raise FabricCLIError()
                    return True

                side_effect_mock.side_effect = is_command_supported_side_effect
                cli_executor.exec_command(
                    f"bulk-export {workspace.full_path} --output {str(tmp_path)} --force --recursive"
                )

            # Assert - should print summary with exported and skipped counts
            mock_print_output.assert_called_once()
            call_kwargs = mock_print_output.call_args
            message = call_kwargs.kwargs.get(
                "message", call_kwargs[1].get("message", "")
            )
            assert "Exported 1 items" in message
            assert "Skipped 1 items due to unsupported item types" in message
            # Unsupported item type should be mentioned in the message
            assert "Environment (1)" in message

        # Assert - only the supported notebook should be exported
        export_path = tmp_path / f"{notebook.display_name}.Notebook"
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == ".py" for file in files)
        assert any(file.name == ".platform" for file in files)

    def test_bulk_export_folder_with_unsupported_items_success(
        self,
        cli_executor,
        workspace,
        folder_factory,
        item_factory,
        tmp_path,
    ):
        # unsupported items are items that are not supported by the bulk-export command, but user has required permissions
        # Setup - create a folder with both supported and unsupported items
        folder = folder_factory(path=workspace.full_path)
        notebook = item_factory(ItemType.NOTEBOOK, path=folder.full_path)
        _ = item_factory(ItemType.ENVIRONMENT, path=folder.full_path)

        with patch("fabric_cli.utils.fab_ui.print_output_format") as mock_print_output:
            # Execute command
            with patch(
                "fabric_cli.utils.fab_cmd_bulk_export_utils.is_command_supported"
            ) as side_effect_mock:
                # Mock is_command_supported to return False for ENVIRONMENT item to simulate unsupported item type
                def is_command_supported_side_effect(element):
                    if element.item_type == ItemType.ENVIRONMENT:
                        raise FabricCLIError()
                    return True

                side_effect_mock.side_effect = is_command_supported_side_effect
                cli_executor.exec_command(
                    f"bulk-export {folder.full_path} --output {str(tmp_path)} --force --recursive"
                )

            # Assert - should print summary with exported and skipped counts
            mock_print_output.assert_called_once()
            call_kwargs = mock_print_output.call_args
            message = call_kwargs.kwargs.get(
                "message", call_kwargs[1].get("message", "")
            )
            assert "Exported 1 items" in message
            assert "Skipped 1 items due to unsupported item types" in message
            # Unsupported item type should be mentioned in the message
            assert "Environment (1)" in message
            data = call_kwargs.kwargs.get("data", call_kwargs[1].get("data", []))
            assert data[0]["exported"] == 1
            assert data[0]["skipped"] == 1

        # Assert - only the supported notebook should be exported
        export_path = (
            tmp_path / folder.display_name / f"{notebook.display_name}.Notebook"
        )
        assert export_path.is_dir()
        files = list(export_path.iterdir())
        assert len(files) == 2
        assert any(file.suffix == ".py" for file in files)
        assert any(file.name == ".platform" for file in files)

    def test_bulk_export_and_deploy_round_trip(
        self, cli_executor, workspace_factory, folder_factory, item_factory, tmp_path
    ):
        # Setup - create a workspace
        origin_ws = workspace_factory()
        dest_ws = workspace_factory()
        # Setup - create a notebook and folder with a data pipeline in the workspace
        folder = folder_factory(path=origin_ws.full_path)
        notebook = item_factory(ItemType.NOTEBOOK, path=origin_ws.full_path)
        data_pipeline = item_factory(ItemType.DATA_PIPELINE, path=folder.full_path)

        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)

        repository_dir_post_deploy = tmp_path / "post_deploy_repo"
        repository_dir_post_deploy.mkdir(parents=True, exist_ok=True)

        # Execute bulk-export command
        cli_executor.exec_command(
            f"bulk-export {origin_ws.full_path} --output {str(repository_dir)} --force --recursive"
        )

        # Execute deploy command on the exported artifacts to the destination workspace
        config_file = _create_config_file(
            tmp_path,
            workspace_name=dest_ws.display_name,
            repository_dir=repository_dir,
        )

        cli_executor.exec_command(f"deploy --config {str(config_file)} --force")

        # bulk-export the destination workspace to verify the artifacts are deployed correctly
        cli_executor.exec_command(
            f"bulk-export {dest_ws.full_path} --output {str(repository_dir_post_deploy)} --force --recursive"
        )
        # Assert - the exported notebook, and data pipeline should exist in the destination workspace
        exported_notebook_path = (
            repository_dir_post_deploy / f"{notebook.display_name}.Notebook"
        )
        assert exported_notebook_path.is_dir()
        exported_data_pipeline_path = (
            repository_dir_post_deploy
            / f"{folder.display_name}"
            / f"{data_pipeline.display_name}.DataPipeline"
        )
        assert exported_data_pipeline_path.is_dir()


def _create_config_file(
    tmp_path,
    *,
    workspace_name,
    repository_dir,
):
    """Helper function for creating deploy configuration files with specified parameters.

    Args:
        tmp_path: Temporary path for file creation
        workspace_name: Name of the workspace
        repository_dir: Path to the repository directory

    Returns:
        Path to the created configuration file
    """
    config_path = tmp_path / "config.yml"

    config_data = {
        "core": {
            "workspace": workspace_name,
            "repository_directory": str(repository_dir),
        },
    }

    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)

    return config_path
