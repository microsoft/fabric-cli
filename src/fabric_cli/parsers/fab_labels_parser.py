# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.labels import fab_labels as labels
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils.fab_util import get_os_specific_command

commands = {
    "Commands": {
        "list-local": "List configured sensitivity labels.",
        "set": "Set a sensitivity label on an item.",
        get_os_specific_command("rm"): "Remove a sensitivity label from an item.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "label", help=fab_constant.COMMAND_LABELS_DESCRIPTION
    )
    parser.set_defaults(func=show_help)
    labels_subparsers = parser.add_subparsers(dest="labels_command")

    # Subcommand for 'set'
    set_examples = [
        "# configure label definitions for CLI (required)",
        "$ config set local_definition_labels <json_path>\n",
        "# set label to an item",
        "$ label set /ws1.Workspace/nb1.Notebook --name Confidential",
    ]

    set_parser = labels_subparsers.add_parser(
        "set",
        help=fab_constant.COMMAND_LABELS_SET_DESCRIPTION,
        fab_examples=set_examples,
        fab_learnmore=["_"],
    )
    set_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    set_parser.add_argument(
        "-n", "--name", metavar="", required=True, help="Label name", nargs="+"
    )
    set_parser.add_argument(
        "-f", "--force", action="store_true", help="Force. Optional"
    )

    set_parser.usage = f"{utils_error_parser.get_usage_prog(set_parser)}"
    set_parser.set_defaults(func=labels.set_command)

    # Subcommand for 'rm'
    rm_aliases = ["del"]
    rm_examples = [
        "# remove label to an item",
        "$ label rm /ws1.Workspace/nb1.Notebook",
    ]

    rm_parser = labels_subparsers.add_parser(
        "rm",
        help=fab_constant.COMMAND_LABELS_RM_DESCRIPTION,
        aliases=rm_aliases,
        fab_examples=rm_examples,
        fab_aliases=rm_aliases,
        fab_learnmore=["_"],
    )
    rm_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    rm_parser.add_argument("-f", "--force", action="store_true", help="Force. Optional")

    rm_parser.usage = f"{utils_error_parser.get_usage_prog(rm_parser)}"
    rm_parser.set_defaults(func=labels.rm_command)

    listlocal_examples = [
        "# list locally defined labels",
        "$ label list-local",
    ]

    listlocal_parser = labels_subparsers.add_parser(
        "list-local",
        help=fab_constant.COMMAND_LABELS_LIST_LOCAL_DESCRIPTION,
        fab_examples=listlocal_examples,
        fab_learnmore=["_"],
    )
    listlocal_parser.usage = f"{utils_error_parser.get_usage_prog(listlocal_parser)}"
    listlocal_parser.set_defaults(func=labels.listlocal_command)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(
        commands, custom_header=fab_constant.COMMAND_LABELS_DESCRIPTION
    )
