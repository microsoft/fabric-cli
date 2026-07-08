# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch


class TestDeployBulkPublish:
    """
    Tests for the --bulk_publish flag wiring into fabric-cicd feature flags.
    These tests mock the fabric-cicd library so they do not require recorded
    HTTP cassettes.
    """

    def _run_deploy(self, tmp_path, bulk_publish, mock_fab_set_state_config):
        """Invoke deploy_with_config_file with fabric-cicd mocked, returning the
        append_feature_flag mock for assertions."""
        from argparse import Namespace

        import fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file as deploy_mod
        from fabric_cli.core import fab_constant

        # disable debug mode so fabric-cicd file logging is disabled during the run
        mock_fab_set_state_config(fab_constant.FAB_DEBUG_ENABLED, "false")

        args = Namespace(
            config=str(tmp_path / "config.yml"),
            target_env="dev",
            params=None,
            bulk_publish=bulk_publish,
        )

        with (
            patch.object(deploy_mod, "append_feature_flag") as mock_flag,
            patch.object(deploy_mod, "deploy_with_config", return_value=None),
            patch.object(deploy_mod, "disable_file_logging"),
            patch.object(deploy_mod, "configure_external_file_logging"),
            patch.object(
                deploy_mod, "create_fabric_token_credential", return_value=None
            ),
        ):
            deploy_mod.deploy_with_config_file(args)

        return mock_flag

    def test_deploy_bulk_publish_enabled_appends_experimental_flags_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --bulk_publish is set, both experimental bulk publish flags are appended."""
        mock_flag = self._run_deploy(tmp_path, True, mock_fab_set_state_config)

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" in appended
        assert "enable_bulk_publish" in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended

    def test_deploy_bulk_publish_disabled_by_default_omits_flags_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --bulk_publish is not set (default), bulk publish flags are not appended."""
        mock_flag = self._run_deploy(tmp_path, False, mock_fab_set_state_config)

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_experimental_features" not in appended
        assert "enable_bulk_publish" not in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended
