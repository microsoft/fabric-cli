# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.acls import fab_acls_get as acls_get
from fabric_cli.commands.acls import fab_acls_ls as acls_ls
from fabric_cli.commands.acls import fab_acls_rm as acls_rm
from fabric_cli.commands.acls import fab_acls_set as acls_set
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context


@handle_exceptions()
@set_command_context()
def ls_command(args: Namespace) -> None:
    _execute_command(args, Command.ACL_LS, acls_ls.exec_command)


@handle_exceptions()
@set_command_context()
def rm_command(args: Namespace) -> None:
    _execute_command(args, Command.ACL_RM, acls_rm.exec_command)


@handle_exceptions()
@set_command_context()
def get_command(args: Namespace) -> None:
    _execute_command(args, Command.ACL_GET, acls_get.exec_command)


@handle_exceptions()
@set_command_context()
def set_command(args: Namespace) -> None:
    _execute_command(args, Command.ACL_SET, acls_set.exec_command)


def _execute_command(args: Namespace, command: Command, exec_func) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(command)
    exec_func(args, context)
