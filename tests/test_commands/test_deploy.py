# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from fabric_cli.core import fab_constant
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_types import ItemType
from tests.test_commands.commands_parser import CLIExecutor


class TestDeploy:
    """
    Test class for deploy command end-to-end scenarios covering success and failure paths.
    Tests use real workspaces and items but mock fabric-cicd library calls.
    """

    def _create_config_file(self, tmp_path, config_name, workspace_name, repository_dir, 
                          item_types=None, parameter_file=None, target_env=None, **extra_config):
        """Create a deployment configuration file with specified parameters."""
        config_path = tmp_path / config_name
        
        # Default item types if not provided
        if item_types is None:
            item_types = ["Notebook"]
        
        config_data = {
            "core": {
                "workspace": {
                    target_env: workspace_name
                } if target_env else workspace_name,
                "repository_directory": f"{str(repository_dir)}",
                "item_types_in_scope": item_types
            },
            "publish": {
                "skip": {
                    target_env: False
                } if target_env else False
            }
        }
        
        # Add parameter file if specified
        if parameter_file:
            config_data["core"]["parameter"] = str(parameter_file)
        
        # Add any extra configuration
        for key, value in extra_config.items():
            config_data.setdefault("core", {})[key] = value
        
        # Write config file
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        return config_path

    def test_deploy_single_item_success(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_print_done,
    ):
        """
        Test successful deployment of a single notebook item.
        """
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)

        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(repository_dir)} --force --format .py"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_basic.yml",
            workspace.display_name,
            repository_dir,
            item_types=["Notebook"]
        )
        
        mock_print_done.reset_mock()
        
        # Execute command
        cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev --force")
        
        # Assert
        mock_print_done.assert_called()
        assert "Config-based deployment completed successfully" in str(mock_print_done.call_args)
  
    # def test_deploy_dependencies_datapipeline_notebook_success(
    #     self,
    #     cli_executor: CLIExecutor,
    #     workspace,
    #     item_factory,
    #     tmp_path,
    #     mock_print_done,
    # ): # Deployment failed: Duplicate logicalId '00000000-0000-0000-0000-000000000000' found in /tmp/pytest-of-vscode/pytest-50/test_deploy_dependencies_datap0/repo/fabcli000002.DataPipeline/.platform
    #     """
    #     Test successful deployment of DataPipeline with Notebook dependency.
    #     """
    #     # Setup
    #     notebook = item_factory(ItemType.NOTEBOOK)
    #     datapipeline = item_factory(ItemType.DATA_PIPELINE)
        
    #     repository_dir = tmp_path / "repo"
    #     repository_dir.mkdir(parents=True, exist_ok=True)
        
    #     cli_executor.exec_command(f"set {datapipeline.full_path} --input  --force")

    #     for item in [notebook, datapipeline]:
    #         cli_executor.exec_command(
    #             f"export {item.full_path} --output {str(repository_dir)} --force"
    #         )
        
    #     config_path = self._create_config_file(
    #         tmp_path,
    #         "config_dependencies.yml",
    #         workspace.display_name,
    #         repository_dir,
    #         item_types=["DataPipeline", "Notebook"]
    #     )

    #     mock_print_done.reset_mock()

    #     # Execute command
    #     cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev --force")
        
    #     # Assert
    #     mock_print_done.assert_called()
    #     assert "Config-based deployment completed successfully" in str(mock_print_done.call_args)

    # def test_deploy_missing_dependency_failure(
    #     self,
    #     cli_executor: CLIExecutor,
    #     workspace,
    #     item_factory,
    #     tmp_path,
    #     mock_fab_ui_print_error,
    # ): # Shira - didn't pass 
    #     """
    #     Test deployment failure when a dependency is missing.
    #     """
    #     # Create only main pipeline, but not the dependency
    #     datapipeline = item_factory(ItemType.DATA_PIPELINE)
        
    #     # Create repository directory and export item
    #     repository_dir = tmp_path / "repo"
    #     repository_dir.mkdir(parents=True, exist_ok=True)
        
    #     cli_executor.exec_command(
    #         f"export {datapipeline.full_path} --output {str(repository_dir)} --force"
    #     )
        
    #     # Create config file
    #     config_path = self._create_config_file(
    #         tmp_path,
    #         "config_missing_dependency.yml",
    #         workspace.display_name,
    #         repository_dir,
    #         item_types=["DataPipeline", "Notebook"]  # Include Notebook but don't export any
    #     )
        
    #     # Reset mock
    #     mock_fab_ui_print_error.reset_mock()
        
    #     # Execute deploy command and expect it to handle missing dependency
    #     cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev --force")
        
    #     # The real deployment may warn about missing items rather than failing

    def test_deploy_config_without_tenv_with_prompt_success(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_print_done,
        mock_questionary_confirm,
    ):
        """
        Test deployment success when config doesn't have target environment but user confirms via prompt.
        """
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)
        
        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(repository_dir)} --force --format .py"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_no_tenv.yml",
            workspace.display_name,
            repository_dir,
            item_types=["Notebook"]
        )
        
        with patch("fabric_cli.utils.fab_ui.prompt_confirm") as mock_prompt:
            mock_prompt.return_value = True
            mock_print_done.reset_mock()
            
            # Execute command
            cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)}")
            
            # Assert
            mock_prompt.assert_called_once()
            assert "Are you sure you want to deploy without specified target environment?" in str(mock_prompt.call_args)
            mock_print_done.assert_called()
            assert "Config-based deployment completed successfully" in str(mock_print_done.call_args)

    def test_deploy_config_with_tenv_without_force_prompt_success(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_print_done,
        mock_questionary_confirm,
    ):
        """
        Test deployment success when config has target environment but no --force flag, user confirms via prompt.
        """
        # Setup
        variable_library = item_factory(ItemType.VARIABLE_LIBRARY)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)
        
        cli_executor.exec_command(
            f"export {variable_library.full_path} --output {str(repository_dir)} --force"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_with_tenv.yml",
            workspace.display_name,
            repository_dir,
            item_types=["VariableLibrary"]
        )
        
        with patch("fabric_cli.utils.fab_ui.prompt_confirm") as mock_prompt:
            mock_prompt.return_value = True
            
            # Reset mock
            mock_print_done.reset_mock()
            
            # Execute command
            cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev")
            
            # Assert
            mock_prompt.assert_called_once()
            assert "Are you sure you want to deploy with the specified configuration file?" in str(mock_prompt.call_args)
            mock_print_done.assert_called()
            assert "Config-based deployment completed successfully" in str(mock_print_done.call_args)


    def test_deploy_config_missing_tenv_failure(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_fab_ui_print_error,
        mock_print_done,
    ):
        """
        Test deployment failure when config is missing target environment and user cancels prompt.
        """
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)
        
        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(repository_dir)} --force --format .py"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_missing_tenv.yml",
            workspace.display_name,
            repository_dir,
            target_env='dev',
            item_types=["Notebook"]
        )
        
        with patch("fabric_cli.utils.fab_ui.prompt_confirm") as mock_prompt:
            mock_prompt.return_value = True
            
            # Reset mock
            mock_fab_ui_print_error.reset_mock()
            mock_print_done.reset_mock()

            # Execute command
            result = cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)}")
            
            # Assert
            mock_prompt.assert_called_once()
            assert "Are you sure you want to deploy without specified target environment?" in str(mock_prompt.call_args)
            mock_fab_ui_print_error.assert_called_once()
            assert "Deployment failed with error" in str(mock_fab_ui_print_error.call_args)
            assert "Configuration contains environment mappings but no environment was provided. Please specify an environment or remove environment mappings" in str(mock_fab_ui_print_error.call_args)
            mock_print_done.assert_not_called()

    def test_deploy_config_without_tenv_cancel_success(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_fab_ui_print_error,
        mock_print_done,
    ):
        """
        Test deployment failure when config is missing target environment and user cancels prompt.
        """
        # Setup
        notebook = item_factory(ItemType.NOTEBOOK)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)
        
        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(repository_dir)} --force --format .py"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_missing_tenv.yml",
            workspace.display_name,
            repository_dir,
            target_env='dev',
            item_types=["Notebook"]
        )
        
        with patch("fabric_cli.utils.fab_ui.prompt_confirm") as mock_prompt:
            mock_prompt.return_value = False
            
            # Reset mock
            mock_fab_ui_print_error.reset_mock()

            # Execute command
            result = cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)}")
            
            # Assert
            mock_prompt.assert_called_once()
            assert "Are you sure you want to deploy without specified target environment?" in str(mock_prompt.call_args)
            # make sure no error nor success messages are printed since deploy was cancelled
            mock_fab_ui_print_error.assert_not_called()
            mock_print_done.assert_not_called()

    def test_deploy_with_config_override_success(
        self,
        cli_executor: CLIExecutor,
        workspace,
        item_factory,
        tmp_path,
        mock_print_done,
    ): # need to verify notebook was deployed and not datapipeline due to config override

        """
        Test deployment success with configuration override.
        """
        # Setup
        notebook = item_factory(ItemType.DATA_PIPELINE)
        
        repository_dir = tmp_path / "repo"
        repository_dir.mkdir(parents=True, exist_ok=True)
        
        cli_executor.exec_command(
            f"export {notebook.full_path} --output {str(repository_dir)} --force"
        )
        
        config_path = self._create_config_file(
            tmp_path,
            "config_override.yml",
            workspace.display_name,
            repository_dir,
            item_types=["DataPipeline"],
            target_env="dev"
        )
        
        mock_print_done.reset_mock()
        
        # Execute command
        config_override = '{"core": {"item_types_in_scope": ["Notebook"]}, "publish": {"skip": {"dev": false}}}'
        cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev -P config_override='{config_override}' --force")
        
        # Assert
        mock_print_done.assert_called()
        assert "Config-based deployment completed successfully" in str(mock_print_done.call_args)

    # def test_deploy_invalid_item_type_config_file_failure(
    #     self,
    #     cli_executor: CLIExecutor,
    #     tmp_path,
    #     mock_fab_ui_print_error,
    #     workspace,
    # ): # no recording since there is no api calls involved here.
    #     """
    #     Test deployment failure when config file contains an invalid item type.
    #     """
    #     #Setup
    #     repository_dir = tmp_path / "repo"
    #     repository_dir.mkdir(parents=True, exist_ok=True)

    #     config_path = self._create_config_file(
    #         tmp_path,
    #         "invalid_config.yml",
    #         workspace.display_name,
    #         repository_dir,
    #         item_types=["Pipeline"],  # Unsupported item type
    #         target_env="dev"
    #     )

    #     # Reset mock
    #     mock_fab_ui_print_error.reset_mock()
        
    #     # Execute command
    #     cli_executor.exec_command(f"deploy --deploy_config_file {str(config_path)} --target_env dev --force")
        
    #     # Assert
    #     mock_fab_ui_print_error.assert_called_once()
    #     assert mock_fab_ui_print_error.call_args[0][0].status_code == fab_constant.ERROR_IN_DEPLOYMENT
    #     assert "Invalid item type 'Pipeline'" in mock_fab_ui_print_error.call_args[0][0].message