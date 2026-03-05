import json
from argparse import Namespace

from fabric_cicd import append_feature_flag, configure_external_file_logging, deploy_with_config, disable_file_logging

from fabric_cli.core import fab_constant, fab_state_config
from fabric_cli.core import fab_logger
from fabric_cli.core.fab_exceptions import FabricCLIError
# from fabric_cli.core.fab_logger import get_logger
from fabric_cli.core.fab_msal_bridge import create_fabric_token_credential
from fabric_cli.utils import fab_ui
from fabric_cli.utils.fab_util import get_dict_from_params


def deploy_with_config_file(args: Namespace) -> None:
    """deploy fabric items to a workspace using a configuration file and target environment - delegates to CICD library."""

    try:
        if fab_state_config.get_config(fab_constant.FAB_DEBUG_ENABLED) == "true":
            cli_logger = fab_logger.get_logger()
            configure_external_file_logging(cli_logger)
        else:
            disable_file_logging()

        # feature flags required for this feature
        append_feature_flag("disable_print_identity")

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
                args, message=result)

    except Exception as e:
        raise FabricCLIError(
            f"Deployment failed: {str(e)}",
            fab_constant.ERROR_IN_DEPLOYMENT)
