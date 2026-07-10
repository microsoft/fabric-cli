# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import patch


class TestDeployShortcutPublish:
    """
    Tests for the --shortcut_publish flag wiring into fabric-cicd feature flags.
    These tests mock the fabric-cicd library so they do not require recorded
    HTTP cassettes.
    """

    def _run_deploy(self, tmp_path, shortcut_publish, mock_fab_set_state_config):
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
            shortcut_publish=shortcut_publish,
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

    def test_deploy_shortcut_publish_enabled_appends_flag_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --shortcut_publish is set, the shortcut publish feature flag is appended."""
        mock_flag = self._run_deploy(tmp_path, True, mock_fab_set_state_config)

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_shortcut_publish" in appended
        # shortcut publish is not experimental and must not enable experimental mode
        assert "enable_experimental_features" not in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended

    def test_deploy_shortcut_publish_disabled_by_default_omits_flag_success(
        self, tmp_path, mock_fab_set_state_config
    ):
        """When --shortcut_publish is not set (default), the flag is not appended."""
        mock_flag = self._run_deploy(tmp_path, False, mock_fab_set_state_config)

        appended = [call.args[0] for call in mock_flag.call_args_list]
        assert "enable_shortcut_publish" not in appended
        # existing behavior is preserved
        assert "disable_print_identity" in appended
