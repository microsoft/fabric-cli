# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file import deploy_with_config_file
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace) -> None:
    """deploy fabric items to a workspace using a configuration file and target environment - CICD flow."""
    if args.force or fab_ui.prompt_confirm(f"Are you sure you want to deploy {'without specified target environment' if args.target_env is None else 'with the specified configuration file'}?"):
        deploy_with_config_file(args)
