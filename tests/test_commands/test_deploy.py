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

    def test_deploy_multiple_items_bulk_publish_enabled_success(
        self,
        deploy_setup_factory,
        cli_executor: CLIExecutor,
        workspace,
        mock_print_done,
        monkeypatch,
    ):
        """
        Test successful deployment of multiple items when the experimental
        deploy_bulk_publish_enabled config setting is turned on.

        The setting is enabled via monkeypatch so it is automatically restored
        when the test finishes, whether it passes or fails. Bulk publish uses a
        different fabric-cicd API path (single bulk import call), so the
        fabric-cicd deploy_with_config call is mocked to avoid recorded HTTP
        cassettes while still exercising the CLI's bulk-publish flag wiring.
        """
        import fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file as deploy_mod
        from fabric_cli.core import fab_constant, fab_state_config

        # Setup
        deploy_config_path = deploy_setup_factory(
            target_env="dev",
            item_types=[ItemType.DATA_PIPELINE,
                        ItemType.NOTEBOOK, ItemType.VARIABLE_LIBRARY]
        )

        # Enable the experimental bulk publish setting only for this test.
        # monkeypatch restores the original get_config on teardown regardless
        # of whether the test passes or fails.
        real_get_config = fab_state_config.get_config

        def fake_get_config(key):
            if key == fab_constant.FAB_DEPLOY_BULK_PUBLISH_ENABLED:
                return "true"
            return real_get_config(key)

        monkeypatch.setattr(fab_state_config, "get_config", fake_get_config)

        mock_print_done.reset_mock()

        # Execute command with fabric-cicd mocked: append_feature_flag is a
        # pure mock so it does not mutate fabric-cicd's global feature-flag
        # state (which would leak into other tests), and deploy_with_config is
        # mocked because bulk publish uses an unrecorded bulk import API path.
        with (
            patch.object(deploy_mod, "append_feature_flag") as mock_flag,
            patch.object(deploy_mod, "deploy_with_config") as mock_deploy,
        ):
            mock_deploy.return_value.message = "Deployment completed successfully"
            cli_executor.exec_command(
                f"deploy --config {str(deploy_config_path)} --target_env dev --force")

        # Assert deployment completed and the bulk publish flags were applied
        mock_print_done.assert_called()
        assert "Deployment completed successfully" in str(
            mock_print_done.call_args)
        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" in appended
        assert "enable_bulk_publish" in appended

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

        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            # Execute command (without --target_env flag)
            cli_executor.exec_command(
                f"deploy --config {str(deploy_config_path)}")

        # Assert
        mock_confirm.assert_called()

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
