# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch

import pytest

from fabric_cli.core.fab_exceptions import FabricCLIError


class TestDeployBulkPublish:
    """
    Tests for the --bulk_publish flag wiring into fabric-cicd feature flags.
    These tests mock the fabric-cicd library so they do not require recorded
    HTTP cassettes.
    """

    def _create_deploy_args(self, tmp_path, bulk_publish):
        """Create arguments for deploy_with_config_file."""
        from argparse import Namespace

        return Namespace(
            config=str(tmp_path / "config.yml"),
            target_env="dev",
            params=None,
            bulk_publish=bulk_publish,
            command_path="deploy",
        )

    def _run_deploy_success(self, tmp_path, bulk_publish, mock_fab_set_state_config):
        """Run a successful deployment and return feature flag mocks."""
        import fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file as deploy_mod
        from fabric_cli.core import fab_constant

        # disable debug mode so fabric-cicd file logging is disabled during the run
        mock_fab_set_state_config(fab_constant.FAB_DEBUG_ENABLED, "false")
        args = self._create_deploy_args(tmp_path, bulk_publish)

        with (
            patch.object(deploy_mod, "append_feature_flag") as mock_flag,
            patch.object(deploy_mod, "remove_feature_flag") as mock_remove_flag,
            patch.object(deploy_mod, "deploy_with_config", return_value=None),
            patch.object(deploy_mod, "disable_file_logging"),
            patch.object(deploy_mod, "configure_external_file_logging"),
            patch.object(
                deploy_mod, "create_fabric_token_credential", return_value=None
            ),
        ):
            deploy_mod.deploy_with_config_file(args)

        return mock_flag, mock_remove_flag

    def _run_deploy_failure(self, tmp_path, bulk_publish, mock_fab_set_state_config):
        """Run a failed deployment and return feature flag mocks."""
        import fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file as deploy_mod
        from fabric_cli.core import fab_constant

        # disable debug mode so fabric-cicd file logging is disabled during the run
        mock_fab_set_state_config(fab_constant.FAB_DEBUG_ENABLED, "false")
        args = self._create_deploy_args(tmp_path, bulk_publish)

        with (
            patch.object(deploy_mod, "append_feature_flag") as mock_flag,
            patch.object(deploy_mod, "remove_feature_flag") as mock_remove_flag,
            patch.object(
                deploy_mod,
                "deploy_with_config",
                side_effect=Exception("Simulated deployment failure"),
            ),
            patch.object(deploy_mod, "disable_file_logging"),
            patch.object(deploy_mod, "configure_external_file_logging"),
            patch.object(
                deploy_mod, "create_fabric_token_credential", return_value=None
            ),
        ):
            with pytest.raises(FabricCLIError):
                deploy_mod.deploy_with_config_file(args)

        return mock_flag, mock_remove_flag

    def test_deploy_bulk_publish_enabled_appends_experimental_flags_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --bulk_publish is set, both experimental bulk publish flags are appended."""
        mock_flag, mock_remove_flag = self._run_deploy_success(
            tmp_path, True, mock_fab_set_state_config
        )

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" in appended
        assert "enable_bulk_publish" in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended
        removed = [call.args[0] for call in mock_remove_flag.call_args_list]
        assert removed == ["enable_experimental_features", "enable_bulk_publish"]

    def test_deploy_bulk_publish_enabled_removes_flags_on_failure(
        self, tmp_path, mock_fab_set_state_config
    ):
        """Bulk publish flags are removed when deployment raises an exception."""
        _, mock_remove_flag = self._run_deploy_failure(
            tmp_path, True, mock_fab_set_state_config
        )

        removed = [call.args[0] for call in mock_remove_flag.call_args_list]
        assert removed == ["enable_experimental_features", "enable_bulk_publish"]

    def test_deploy_bulk_publish_disabled_by_default_omits_flags_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --bulk_publish is not set, bulk publish flags are not changed."""
        mock_flag, mock_remove_flag = self._run_deploy_success(
            tmp_path, False, mock_fab_set_state_config
        )

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" not in appended
        assert "enable_bulk_publish" not in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended
        mock_remove_flag.assert_not_called()
