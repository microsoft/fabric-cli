from fabric_cicd import append_feature_flag, change_log_level, deploy_with_config
from argparse import Namespace

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core.fab_auth import FabAuth
from fabric_cli.utils import fab_ui

from fabric_cli.core.fab_msal_bridge import create_fabric_token_credential  # type: ignore


def deploy_with_config_file(args: Namespace) -> None:
    """deploy fabric items to a workspace using a configuration file and target environment - delegates to CICD library."""

    try:
        if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) == "true":
            # Set CICD library log level to debug if FAB_DEBUG is enabled in Fabric CLI
            change_log_level()

        # feature flags required for this feature
        append_feature_flag("enable_experimental_features")
        append_feature_flag("enable_config_deploy")
        append_feature_flag("enable_response_collection")

        # root_directory = Path(__file__).resolve().parent.parent.parent.parent

        # sys.path.insert(0, str(root_directory / "src"))
        # str(root_directory / "sample" / "config.yml")
        deplo_config_file = args.deploy_config_file

        result = deploy_with_config(
            config_file_path=deplo_config_file,
            environment=args.target_env,
            token_credential=create_fabric_token_credential(
                fab_auth=FabAuth()),  # MSAL bridge TokenCredential
        )

        if result:
            fab_ui.print_output_format(
                args, message=result)

    except Exception as e:
        raise Exception(f"Deployment failed with error: {str(e)}")
