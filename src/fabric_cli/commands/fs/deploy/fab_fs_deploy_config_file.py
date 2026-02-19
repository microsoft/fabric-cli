from argparse import Namespace

from fabric_cli.utils import fab_ui

def deploy_with_config_file(args: Namespace) -> None:
    """Deploy using config file and environment parameters - delegates to CICD library."""
    # WILL BE REMOVED - SHOULD CALL DEPLOY_WITH_CONFIG 
    fab_ui.print_info(
        "Deploying using config file and environment parameters..." + str(args))
