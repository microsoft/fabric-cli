# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import platform
from unittest.mock import patch

import pytest
import yaml

from fabric_cli.core.fab_types import ItemType
from tests.test_commands.commands_parser import CLIExecutor
from tests.test_commands.conftest import mock_print_done


class TestDeploy:
    """
    Test class for deploy command end-to-end scenarios covering success and failure paths.
    Tests use real workspaces and items but mock fabric-cicd library calls.
    """

    def test_deploy_single_item_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_print_done,
    ):
        """
        Test successful deployment of a single notebook item.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.NOTEBOOK]
        )
        
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)} --target_env dev --force")

        # Assert
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)

    def test_deploy_multiple_items_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        workspace,
        mock_print_done,
    ):
        """
        Test successful deployment of multiple items (DataPipeline, Notebook, VariableLibrary).
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.DATA_PIPELINE,
                        ItemType.NOTEBOOK, ItemType.VARIABLE_LIBRARY]
        )

        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)} --target_env dev --force")

        # Assert
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)

    def test_deploy_config_without_tenv_with_prompt_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_print_done,
        mock_questionary_confirm,
    ):
        """
        Test deployment success when config doesn't have target environment but user confirms via prompt.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env=None,
            item_types=[ItemType.NOTEBOOK]
        )
        
        mock_questionary_confirm.return_value = True
        mock_print_done.reset_mock()
            
        # Execute command
        cli_executor.exec_command(
            f"deploy --config {deploy_config_path}")

        # Assert
        mock_questionary_confirm.assert_called_once()
        assert "Are you sure you want to deploy without a target environment using the specified configuration file?" in str(
            mock_questionary_confirm.call_args)
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)

    def test_deploy_config_with_tenv_without_force_prompt_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_print_done,
        mock_questionary_confirm,
    ):
        """
        Test deployment success when config has target environment but no --force flag, user confirms via prompt.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.VARIABLE_LIBRARY]
        )

        # Reset mock
        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)} --target_env dev")

        # Assert
        mock_questionary_confirm.assert_called_once()
        assert "Are you sure you want to deploy to target environment 'dev' using the specified configuration file?" in str(
            mock_questionary_confirm.call_args)
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)

    def test_deploy_config_missing_tenv_failure(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_fab_ui_print_error,
        mock_print_done,
        mock_questionary_confirm
    ):
        """
        Test deployment failure when config is missing target environment and user cancels prompt.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.NOTEBOOK]
        )

        # Reset mock
        mock_fab_ui_print_error.reset_mock()
        mock_print_done.reset_mock()

        # Execute command (without --target_env flag)
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)}")

        # Assert
        mock_questionary_confirm.assert_called_once()
        assert 'Are you sure you want to deploy without a target environment using the specified configuration file?' in str(
            mock_questionary_confirm.call_args)
        mock_fab_ui_print_error.assert_called_once()
        assert "Deployment failed" in str(
            mock_fab_ui_print_error.call_args)
        assert "Configuration contains environment mappings but no environment was provided. Please specify an environment or remove environment mappings" in str(
            mock_fab_ui_print_error.call_args)
        mock_print_done.assert_not_called()

    def test_deploy_config_without_tenv_cancel_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_fab_ui_print_error,
        mock_print_done,
        mock_questionary_confirm
    ):
        """
        Test deployment failure when config is missing target environment and user cancels prompt.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.NOTEBOOK]
        )

        # Reset mock
        mock_fab_ui_print_error.reset_mock()
        mock_print_done.reset_mock()

        # Execute command (without --target_env flag)
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)}")

        # Assert
        mock_questionary_confirm.assert_called_once()
        assert "Are you sure you want to deploy without a target environment using the specified configuration file?" in str(
            mock_questionary_confirm.call_args)
            # make sure no error nor success messages are printed since deploy was cancelled
        mock_fab_ui_print_error.assert_not_called()
        mock_print_done.assert_not_called()

    def test_deploy_with_config_override_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_print_done,
    ):
        """
        Test deployment success with configuration override.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.DATA_PIPELINE]
        )

        mock_print_done.reset_mock()

        # Execute command
        config_override = '{"core": {"item_types_in_scope": ["Notebook"]}, "publish": {"skip": {"dev": false}}}'
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)} --target_env dev -P config_override='{config_override}' --force")

        # Assert
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)

    def test_deploy_invalid_config_file_path_failure(
        self,
        cli_executor: CLIExecutor,
        mock_fab_ui_print_error,
        tmp_path,
    ):
        """
            Test deployment failure when config file path is invalid/doesn't exist.
            """
        # Create a non-existent config path
        invalid_config_path = tmp_path / "non_existent_config.yml"

        # Reset mock
        mock_fab_ui_print_error.reset_mock()

        # Execute command with invalid config path
        cli_executor.exec_command(
            f"deploy --config {str(invalid_config_path)} --force")

        # Assert that error is printed
        mock_fab_ui_print_error.assert_called()
        assert "Configuration validation failed with 1 error(s):\n  - Configuration file not found" in mock_fab_ui_print_error.call_args[
            0][0].message

    def test_deploy_invalid_config_file_failure(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        mock_fab_ui_print_error,
    ):
        """
        Test deployment failure with invalid configuration file.
        """
        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.DATA_PIPELINE]
        )

        mock_fab_ui_print_error.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"deploy --config {str(deploy_config_path)} --target_env test --force")

        # Assert
        mock_fab_ui_print_error.assert_called()
        assert "Environment 'test' not found in 'core.workspace' mappings. Available: ['dev']" in mock_fab_ui_print_error.call_args[0][0].message

    def test_deploy_with_home_directory_path_success(
        self,
        cli_executor: CLIExecutor,
        mock_print_done,
        tmp_path,
        monkeypatch,
        deploy_setup_factory
    ):
        """
        Test deployment success when repository path contains ~ (home directory).
        """
        # Setup mock home directory
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_dir_env = "USERPROFILE" if platform.system() == "Windows" else "HOME"

        # Mock the HOME environment variable
        monkeypatch.setenv(home_dir_env, str(home_dir))

        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.DATA_PIPELINE],
            path_override=str(home_dir)
        )

        mock_print_done.reset_mock()

        # Execute command
        cli_executor.exec_command(
            f"deploy --config {deploy_config_path} --target_env dev --force")

        # Assert
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)
