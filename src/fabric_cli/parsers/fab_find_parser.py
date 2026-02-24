# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Parser for the find command."""

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.find import fab_find as find
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui


COMMAND_FIND_DESCRIPTION = "Search the Fabric catalog for items."

commands = {
    "Description": {
        "find": "Search across all workspaces by name, description, or workspace name.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    """Register the find command parser."""
    examples = [
        "# search for items by name or description",
        "$ find 'sales report'\n",
        "# search for lakehouses only",
        "$ find 'data' -P type=Lakehouse\n",
        "# search for multiple item types",
        "$ find 'dashboard' -P type=Report,SemanticModel\n",
        "# show detailed output with IDs",
        "$ find 'sales' -l\n",
        "# combine filters",
        "$ find 'finance' -P type=Warehouse,Lakehouse -l",
    ]

    parser = subparsers.add_parser(
        "find",
        help=COMMAND_FIND_DESCRIPTION,
        fab_examples=examples,
        fab_learnmore=["_"],
    )

    parser.add_argument(
        "query",
        help="Search text (matches display name, description, and workspace name)",
    )
    parser.add_argument(
        "-P",
        "--params",
        required=False,
        metavar="",
        nargs="*",
        help="Parameters in key=value format. Supported: type=<ItemType>[,<ItemType>...]",
    )
    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Show detailed output. Optional",
    )

    parser.usage = f"{utils_error_parser.get_usage_prog(parser)}"
    parser.set_defaults(func=find.find_command)


def show_help(args: Namespace) -> None:
    """Display help for the find command."""
    utils_ui.display_help(commands, custom_header=COMMAND_FIND_DESCRIPTION)
