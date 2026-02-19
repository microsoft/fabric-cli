# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.fs.deploy.fab_fs_deploy_config_file import deploy_with_config_file 
from fabric_cli.core.hiearchy.fab_element import FabricElement
from fabric_cli.utils import fab_ui


def exec_command(args: Namespace, context: FabricElement) -> None:
    """Deploy using config file and environment parameters - CICD flow."""
    if args.force or fab_ui.prompt_confirm():
        deploy_with_config_file(args)
