# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.tables import fab_tables as tables
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui

commands = {
    "Commands": {
        "load": "Load data into a lakehouse table.",
        "optimize": "Optimize a Delta table.",
        "schema": "Show the schema of a Delta table.",
        "vacuum": "Vacuum a Delta table by removing old files.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "table", help=fab_constant.COMMAND_TABLES_DESCRIPTION
    )
    parser.set_defaults(func=show_help)
    tables_subparsers = parser.add_subparsers(dest="tables_command")

    # Subcommand for 'schema'
    schema_examples = [
        "# show Delta Lake table schema (lakehouse)",
        "$ table schema /ws1.Workspace/lh1.Lakehouse/Tables/tdeltacsv\n",
        "# show Delta Lake table schema (warehouse)",
        "$ table schema wh1.Warehouse/Tables/dbo/tdelta",
    ]

    schema_parser = tables_subparsers.add_parser(
        "schema",
        help="Shows the schema of a Delta Lake table",
        fab_examples=schema_examples,
        fab_learnmore=["_"],
    )
    schema_parser.add_argument("path", nargs="+", help="Path to the Delta Lake table")

    schema_parser.usage = f"{utils_error_parser.get_usage_prog(schema_parser)}"
    schema_parser.set_defaults(func=tables.schema_command)

    # Subcommand for 'load'
    load_examples = [
        "# load table recursively",
        "$ table load Tables/tdeltacsv --file Files/csv\n",
        "# load parquet, append mode",
        "$ table load Tables/tdeltaparquet --file Files/parquet --format format=parquet --mode append\n",
    ]

    load_parser = tables_subparsers.add_parser(
        "load",
        help="Load data into a new or existing table",
        fab_examples=load_examples,
        fab_learnmore=["_"],
    )
    load_parser.add_argument(
        "path", nargs="+", help="Path to the Delta Lake table (Lakehouse only)"
    )
    load_parser.add_argument(
        "--file", nargs="+", required=True, help="Path to the file or directory to load"
    )
    load_parser.add_argument(
        "--extension", metavar="", help="File extension to filter files. Optional"
    )
    load_parser.add_argument(
        "--mode",
        metavar="",
        choices=["append", "overwrite"],
        default="overwrite",
        required=False,
        help="Mode to load the data (append, overwrite). Optional, default: overwrite",
    )
    load_parser.add_argument(
        "--format",
        metavar="",
        help="Format options in key=value format, separated by commas. Optional, default: format=csv,header=true,delimiter=','",
    )
    load_parser.usage = f"{utils_error_parser.get_usage_prog(load_parser)}"
    load_parser.set_defaults(func=tables.load_command)

    # Subcommand for 'vacuum'
    vacuum_examples = [
        "# vacuum a table (defaul 7 days)",
        "$ table vacuum Tables/tdelta\n",
        "# vacuum a table, custom retention period in hours",
        "$ table vacuum Tables/tdelta --retain_n_hours 182\n",
    ]

    vacuum_parser = tables_subparsers.add_parser(
        "vacuum",
        help="Vacuum a Delta Lake table",
        fab_examples=vacuum_examples,
        fab_learnmore=["_"],
    )
    vacuum_parser.add_argument(
        "path", nargs="+", help="Path to the Delta Lake table (Lakehouse only)"
    )
    vacuum_parser.add_argument(
        "--retain_n_hours",
        metavar="",
        default="168",
        help="Retention period in hours. Optional, default: 168 (7 days)",
    )

    vacuum_parser.usage = f"{utils_error_parser.get_usage_prog(vacuum_parser)}"
    vacuum_parser.set_defaults(func=tables.vacuum_command)

    # Subcommand for 'optimize'
    optimize_examples = [
        "# run table optimize compaction",
        "$ table optimize Tables/tdelta\n",
        "# run table optimize with vorder and zorder",
        "$ table optimize Tables/tdelta --vorder --zorder col1,col2\n",
    ]

    optimize_parser = tables_subparsers.add_parser(
        "optimize",
        help="Optimize a Delta Lake table",
        fab_examples=optimize_examples,
        fab_learnmore=["_"],
    )
    optimize_parser.add_argument(
        "path", nargs="+", help="Path to the Delta Lake table (Lakehouse only)"
    )
    optimize_parser.add_argument(
        "--vorder",
        action="store_true",
        help="Enable V-Order. Optional",
    )
    optimize_parser.add_argument(
        "--zorder",
        metavar="",
        help="List of columns to Z-Order by, separated by commas. Optional",
    )

    optimize_parser.usage = f"{utils_error_parser.get_usage_prog(optimize_parser)}"
    optimize_parser.set_defaults(func=tables.optimize_command)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(
        commands, custom_header=fab_constant.COMMAND_TABLES_DESCRIPTION
    )
