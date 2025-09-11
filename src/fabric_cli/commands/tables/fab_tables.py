# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from argparse import Namespace

from fabric_cli.commands.tables import fab_tables_load as tables_load
from fabric_cli.commands.tables import fab_tables_opt as tables_opt
from fabric_cli.commands.tables import fab_tables_schema as tables_schema
from fabric_cli.core import fab_handle_context as handle_context
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_decorators import handle_exceptions, set_command_context
from fabric_cli.core.hiearchy.fab_onelake_element import OneLakeItem
from fabric_cli.utils import fab_cmd_table_utils as utils_table
from fabric_cli.utils import fab_ui as utils_ui


@handle_exceptions()
@set_command_context()
def schema_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.TABLE_SCHEMA)
    assert isinstance(context, OneLakeItem)
    utils_table.add_table_props_to_args(args, context)
    utils_ui.print_grey(f"Getting schema for '{args.table_name}' table...")
    tables_schema.exec_command(args)


@handle_exceptions()
@set_command_context()
def load_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path, raise_error=False)
    context.check_command_support(Command.TABLE_LOAD)
    assert isinstance(context, OneLakeItem)
    args.wait = True
    utils_table.add_table_props_to_args(args, context)
    utils_ui.print_grey(f"Loading '{args.table_name}' table. It may take some time...")
    tables_load.exec_command(args, context)


@handle_exceptions()
@set_command_context()
def vacuum_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.TABLE_VACUUM)
    assert isinstance(context, OneLakeItem)
    args.wait = True
    utils_table.add_table_props_to_args(args, context)
    retention_period = utils_table.convert_hours_to_dhhmmss(args.retain_n_hours)
    vacuum_config = {
        "vacuumSettings": {"retentionPeriod": retention_period},
    }
    args.configuration = json.dumps(vacuum_config)
    utils_ui.print_grey(
        f"Vacuuming the '{args.table_name}' table. It may take some time..."
    )
    tables_opt.exec_command(args)


@handle_exceptions()
@set_command_context()
def optimize_command(args: Namespace) -> None:
    context = handle_context.get_command_context(args.path)
    context.check_command_support(Command.TABLE_OPTIMIZE)
    assert isinstance(context, OneLakeItem)
    args.wait = True
    utils_table.add_table_props_to_args(args, context)
    optimize_config: dict = {"optimizeSettings": {}}

    if args.vorder:
        optimize_config["optimizeSettings"]["vOrder"] = args.vorder

    if args.zorder:
        zorder_list = [item.strip() for item in args.zorder.split(",")]
        optimize_config["optimizeSettings"]["zOrderBy"] = zorder_list

    args.configuration = json.dumps(optimize_config)
    utils_ui.print_grey(
        f"Optimizing the '{args.table_name}' table. It may take some time..."
    )
    tables_opt.exec_command(args)
