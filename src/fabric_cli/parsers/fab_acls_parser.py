# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.acls import fab_acls as acls
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils.fab_util import get_os_specific_command

commands = {
    "Commands": {
        get_os_specific_command("ls"): "List ACLs for a workspace, item, or OneLake.",
        get_os_specific_command(
            "rm"
        ): "Remove an ACL from a workspace, gateway or connection.",
        "set": "Set access controls on a workspace.",
        "get": "Get ACL details for a workspace, item or OneLake.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("acl", help=fab_constant.COMMAND_ACLS_DESCRIPTION)
    parser.set_defaults(func=show_help)
    acls_subparsers = parser.add_subparsers(dest="acl_subcommand")

    # Subcommand for 'ls'
    ls_aliases = ["dir"]
    ls_examples = [
        "# list acl entries for a workspace",
        f"$ acl ls ws1.Workspace\n",
        "# list acl entries for an item",
        "$ acl ls ws1.Workspace/lh1.Lakehouse -l",
    ]

    ls_parser = acls_subparsers.add_parser(
        "ls",
        aliases=ls_aliases,
        help=fab_constant.COMMAND_ACLS_LS_DESCRIPTION,
        fab_examples=ls_examples,
        fab_aliases=ls_aliases,
        fab_learnmore=["_"],
    )
    ls_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    ls_parser.add_argument(
        "-l",
        "--long",
        required=False,
        action="store_true",
        help="Show detailed output. Optional",
    )
    ls_parser.add_argument(
        "-q",
        "--query",
        metavar="",
        nargs="+",
        required=False,
        help="Query to filter results. Optional",
    )

    ls_parser.usage = f"{utils_error_parser.get_usage_prog(ls_parser)}"
    ls_parser.set_defaults(func=acls.ls_command)

    # Subcommand for 'rm'
    rm_aliases = ["del"]
    rm_examples = [
        "# remove permissions for an identity in a workspace",
        "$ acl rm ws1.Workspace -I <upn | clientId>\n",
    ]

    rm_parser = acls_subparsers.add_parser(
        "rm",
        aliases=rm_aliases,
        help=fab_constant.COMMAND_ACLS_RM_DESCRIPTION,
        fab_examples=rm_examples,
        fab_aliases=rm_aliases,
        fab_learnmore=["_"],
    )
    rm_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    rm_parser.add_argument(
        "-I",
        "--identity",
        metavar="",
        required=True,
        help="Entra identity upn, clientId, objectId or groupName",
    )
    rm_parser.add_argument("-f", "--force", action="store_true", help="Force. Optional")

    rm_parser.usage = f"{utils_error_parser.get_usage_prog(rm_parser)}"
    rm_parser.set_defaults(func=acls.rm_command)

    # Subcommand for 'get'
    get_examples = [
        "# get workspace acl details",
        f"$ acl get ws1.Workspace\n",
        "# run JMESPath query",
        "$ acl get ws1.Workspace -q [*].principal -o /ws1.Workspace/lh1.Lakehouse/Files",
    ]

    get_parser = acls_subparsers.add_parser(
        "get",
        help=fab_constant.COMMAND_ACLS_GET_DESCRIPTION,
        fab_examples=get_examples,
        fab_learnmore=["_"],
    )
    get_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    get_parser.add_argument(
        "-q",
        "--query",
        metavar="",
        nargs="+",
        required=False,
        help="JMESPath query to filter. Optional",
    )
    get_parser.add_argument(
        "-o",
        "--output",
        metavar="",
        required=False,
        help="Output path for export. Optional",
    )

    get_parser.usage = f"{utils_error_parser.get_usage_prog(get_parser)}"
    get_parser.set_defaults(func=acls.get_command)

    # Subcommand for 'set'
    set_examples = [
        "# add or update a workspace role assignment",
        "$ acl set ws1.Workspace -I <objectId> -R <member>\n",
    ]

    set_parser = acls_subparsers.add_parser(
        "set",
        help=fab_constant.COMMAND_ACLS_SET_DESCRIPTION,
        fab_examples=set_examples,
        fab_learnmore=["_"],
    )
    set_parser.add_argument("path", nargs="+", type=str, help="Directory path")
    set_parser.add_argument(
        "-I",
        "--identity",
        metavar="",
        required=True,
        help="Entra identity objectId",
    )
    set_parser.add_argument(
        "-R",
        "--role",
        metavar="",
        required=True,
        help="Role to assign. Use Admin, Member, Contributor, Viewer for workspaces, Owner, User, UserWithReshare for connections, or Admin, ConnectionCreator, ConnectionCreatorWithResharing for gateways",
    )
    set_parser.add_argument(
        "-f", "--force", action="store_true", help="Force. Optional"
    )

    set_parser.usage = f"{utils_error_parser.get_usage_prog(set_parser)}"
    set_parser.set_defaults(func=acls.set_command)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(commands, custom_header=fab_constant.COMMAND_ACLS_DESCRIPTION)
