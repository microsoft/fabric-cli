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


class TestDeployBulkPublish:
    """
    Tests for the deploy_bulk_publish_enabled config setting wiring into
    fabric-cicd feature flags. These tests mock the fabric-cicd library so
    they do not require recorded HTTP cassettes.
    """

    def _run_deploy(self, tmp_path, bulk_value):
        """Invoke deploy_with_config_file with fabric-cicd mocked, returning the
        append_feature_flag mock for assertions."""
        from argparse import Namespace

        import fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file as deploy_mod
        from fabric_cli.core import fab_constant

        args = Namespace(
            config=str(tmp_path / "config.yml"),
            target_env="dev",
            params=None,
        )

        def fake_get_config(key):
            if key == fab_constant.FAB_DEPLOY_BULK_PUBLISH_ENABLED:
                return bulk_value
            if key == fab_constant.FAB_DEBUG_ENABLED:
                return "false"
            return None

        with (
            patch.object(deploy_mod, "append_feature_flag") as mock_flag,
            patch.object(deploy_mod, "deploy_with_config", return_value=None),
            patch.object(deploy_mod, "disable_file_logging"),
            patch.object(deploy_mod, "configure_external_file_logging"),
            patch.object(
                deploy_mod, "create_fabric_token_credential", return_value=None
            ),
            patch.object(
                deploy_mod.fab_state_config, "get_config", side_effect=fake_get_config
            ),
        ):
            deploy_mod.deploy_with_config_file(args)

        return mock_flag

    def test_deploy_bulk_publish_enabled_appends_experimental_flags(self, tmp_path):
        """When the setting is 'true', both experimental bulk publish flags are appended."""
        mock_flag = self._run_deploy(tmp_path, "true")

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" in appended
        assert "enable_bulk_publish" in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended

    def test_deploy_bulk_publish_disabled_by_default_omits_flags(self, tmp_path):
        """When the setting is 'false' (default), bulk publish flags are not appended."""
        mock_flag = self._run_deploy(tmp_path, "false")

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" not in appended
        assert "enable_bulk_publish" not in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended
