# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace

from fabric_cli.commands.jobs import fab_jobs_run as jobs_run
from fabric_cli.commands.jobs import fab_jobs_run_cancel as jobs_run_cancel
from fabric_cli.commands.jobs import fab_jobs_run_list as jobs_run_list
from fabric_cli.commands.jobs import fab_jobs_run_sch as jobs_run_sch
from fabric_cli.commands.jobs import fab_jobs_run_status as jobs_run_status
from fabric_cli.commands.jobs import fab_jobs_run_update as jobs_run_update
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.hiearchy.fab_item import Item
from fabric_cli.utils import fab_cmd_job_utils as utils_job
from fabric_cli.utils import fab_ui


@handle_exceptions()
@set_command_context()
def run_command(args: Namespace) -> None:
    utils_job.validate_timeout_polling_interval(args)
    
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context)
    if args.jobs_command == "start":
        fab_ui.print_grey(f"Starting job (async) for '{args.item}'...")
        args.wait = False
    if args.jobs_command == "run":
        fab_ui.print_grey(f"Running job (sync) for '{args.item}'...")
        args.wait = True
    jobs_run.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def run_list_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN_LIST)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    jobs_run_list.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def run_cancel_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN_CANCEL)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    jobs_run_cancel.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def run_sch_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN_SCH)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context, schedule=True)
    jobs_run_sch.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def run_status_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN_STATUS)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    jobs_run_status.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def run_update_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.JOB_RUN_UPDATE)
    assert isinstance(context, Item)
    utils_job.add_item_props_to_args(args, context)
    utils_job.build_config_from_args(args, context, schedule=True)
    jobs_run_update.exec_command(args, context)
