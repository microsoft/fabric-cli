# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Parser for the find command."""

import argparse
from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.find import fab_find as find
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui


COMMAND_FIND_DESCRIPTION = "Search the Fabric catalog for items."

commands = {
    "Description": {
        "find": "Search across all workspaces by name, description, or workspace name.",
    },
}


def _limit_type(value: str) -> int:
    """Validate --limit is between 1 and 1000."""
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: '{value}'")
    if ivalue < 1 or ivalue > 1000:
        raise argparse.ArgumentTypeError(f"must be between 1 and 1000, got {ivalue}")
    return ivalue


def register_parser(subparsers: _SubParsersAction) -> None:
    """Register the find command parser."""
    examples = [
        "# search for items by name or description",
        "$ find 'sales report'\n",
        "# search for lakehouses only",
        "$ find 'data' --type Lakehouse\n",
        "# search for multiple item types",
        "$ find 'dashboard' --type Report SemanticModel\n",
        "# show detailed output with IDs",
        "$ find 'sales' -l\n",
        "# combine filters",
        "$ find 'finance' --type Warehouse Lakehouse --limit 20",
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
    type_arg = parser.add_argument(
        "--type",
        nargs="+",
        metavar="TYPE",
        help="Filter by item type(s). Examples: Report, Lakehouse, Warehouse. Use <TAB> for full list.",
    )
    # Add tab-completion for item types
    type_arg.completer = find.complete_item_types

    parser.add_argument(
        "--limit",
        metavar="N",
        type=_limit_type,
        default=50,
        help="Maximum number of results to return (1-1000, default: 50)",
    )
    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Show detailed output. Optional",
    )
    parser.add_argument(
        "--continue",
        dest="continue_token",
        metavar="TOKEN",
        help="Continuation token from previous search to get next page of results",
    )

    parser.usage = f"{utils_error_parser.get_usage_prog(parser)}"
    parser.set_defaults(func=find.find_command)


def show_help(args: Namespace) -> None:
    """Display help for the find command."""
    utils_ui.display_help(commands, custom_header=COMMAND_FIND_DESCRIPTION)
