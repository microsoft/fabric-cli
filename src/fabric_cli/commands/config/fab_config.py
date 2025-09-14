# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.config import fab_config_clear_cache as config_clear_cache
from fabric_cli.commands.config import fab_config_get as config_get
from fabric_cli.commands.config import fab_config_ls as config_ls
from fabric_cli.commands.config import fab_config_set as config_set
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context


@handle_exceptions()
@set_command_context()
def set_config(args: Namespace) -> None:
    config_set.exec_command(args)


@handle_exceptions()
@set_command_context()
def get_config(args: Namespace) -> None:
    config_get.exec_command(args)


@handle_exceptions()
@set_command_context()
def list_configs(args: Namespace) -> None:
    config_ls.exec_command(args)


@handle_exceptions()
@set_command_context()
def clear_cache(args: Namespace) -> None:
    config_clear_cache.exec_command(args)
