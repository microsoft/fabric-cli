# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file import deploy_with_config_file
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace) -> None:
    """deploy fabric items to a workspace using a configuration file and target environment - CICD flow."""
    prompt = f"Are you sure you want to deploy {'without a target environment' if args.target_env == 'N/A' else f'to target environment \'{args.target_env}\''} using the specified configuration file?"
    if args.force or fab_ui.prompt_confirm(prompt):
        deploy_with_config_file(args)
