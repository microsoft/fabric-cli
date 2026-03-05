

import json

from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_msal_bridge import create_fabric_token_credential
from fabric_cli.utils import fab_ui
from fabric_cli.core import fab_constant, fab_state_config
from fabric_cicd import append_feature_flag, change_log_level, deploy_with_config
from argparse import Namespace

from fabric_cli.utils.fab_util import get_dict_from_params



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

        deploy_config_file = args.config
        deploy_parameters = get_dict_from_params(args.params, max_depth=1)
        for param in deploy_parameters:
            if isinstance(deploy_parameters[param], str):
                try:
                    deploy_parameters[param] = json.loads(
                        deploy_parameters[param])
                except json.JSONDecodeError:
                    # If it's not a valid JSON string, keep it as is
                    pass
        result = deploy_with_config(
            config_file_path=deploy_config_file,
            environment=args.target_env,
            token_credential=create_fabric_token_credential(),  # MSAL bridge TokenCredential
            **deploy_parameters
        )

        if result:
            fab_ui.print_output_format(
                args, message=result.message)

    except Exception as e:
        raise FabricCLIError(
            f"Deployment failed: {str(e)}",
            fab_constant.ERROR_IN_DEPLOYMENT)
