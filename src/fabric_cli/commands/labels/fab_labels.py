# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.labels import fab_labels_list_local as labels_list_local
from fabric_cli.commands.labels import fab_labels_rm as labels_rm
from fabric_cli.commands.labels import fab_labels_set as labels_set
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.utils import fab_cmd_label_utils as utils_label
from fabric_cli.utils import fab_util as utils


@handle_exceptions()
@set_command_context()
def set_command(args: Namespace) -> None:
    args.name = utils.process_nargs(args.name)
    _execute_command(args, Command.LABEL_SET, labels_set.exec_command)


@handle_exceptions()
@set_command_context()
def rm_command(args: Namespace) -> None:
    _execute_command(args, Command.LABEL_RM, labels_rm.exec_command)


@handle_exceptions()
@set_command_context()
def listlocal_command(args: Namespace) -> None:
    exists = utils_label.read_labels_definition(args)
    if exists:
        labels_list_local.exec_command(args)


def _execute_command(args: Namespace, command: Command, exec_func) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(command)
    exists = utils_label.read_labels_definition(args)
    if exists:
        exec_func(args, context)
