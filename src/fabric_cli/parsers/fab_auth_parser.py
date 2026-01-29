# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.auth import fab_auth as auth
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui

commands = {
    "Commands": {
        "login": "Log in to a Fabric account.",
        "logout": "End the current authentication session.",
        "status": "Display active account and authentication state.",
    },
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("auth", help=fab_constant.COMMAND_AUTH_DESCRIPTION)
    parser.set_defaults(func=show_help)
    auth_subparsers = parser.add_subparsers(dest="auth_command", required=False)

    # Subcommand for 'login'
    login_examples = [
        "# interactive mode",
        "$ auth login\n",
        "# command_line mode",
        "$ fab auth login\n",
        "# command_line mode using service principal auth",
        "$ fab auth login -u <client_id> -p <client_secret> --tenant <tenant_id>\n",
        "# command_line mode using system assigned managed identity auth",
        "$ fab auth login --identity\n",
        "# command_line mode using user assigned managed identity auth",
        "$ fab auth login -i -u <client_id>",
    ]

    login_parser = auth_subparsers.add_parser(
        "login",
        help="Execute login command.",
        fab_examples=login_examples,
        fab_learnmore=["_"],
    )
    login_parser.add_argument(
        "-u",
        "--username",
        metavar="",
        required=False,
        help="Client ID. Optional, only for service principal or system assigned managed identity auth",
    )
    login_parser.add_argument(
        "-p",
        "--password",
        metavar="",
        required=False,
        help="Client password. Optional, only for service principal auth",
    )
    login_parser.add_argument(
        "-t",
        "--tenant",
        metavar="",
        required=False,
        help="Tenant ID. Optional.",
    )
    login_parser.add_argument(
        "-I",
        "--identity",
        required=False,
        action="store_true",
        help="Use managed identity. Optional, only for managed identity auth",
    )
    login_parser.add_argument(
        "--certificate",
        metavar="",
        required=False,
        help="Path to the pem certificate file. Optional, only for service principal auth",
    )
    login_parser.add_argument(
        "--federated-token",
        metavar="",
        required=False,
        help="Federated token that can be used for OIDC token exchange. Optional, only for service principal auth",
    )

    login_parser.usage = f"{utils_error_parser.get_usage_prog(login_parser)}"
    login_parser.set_defaults(func=auth.init)

    # Subcommand for 'logout'
    logout_examples = [
        "# interactive mode",
        "$ auth logout\n",
        "# command_line mode",
        "$ fab auth logout",
    ]

    logout_parser = auth_subparsers.add_parser(
        "logout",
        help="Execute logout command.",
        fab_examples=logout_examples,
        fab_learnmore=["_"],
    )

    logout_parser.usage = f"{utils_error_parser.get_usage_prog(logout_parser)}"
    logout_parser.set_defaults(func=auth.logout)

    # Subcommand for 'status'
    status_examples = [
        "# interactive mode",
        "$ auth status\n",
        "# command_line mode",
        "$ fab auth status",
    ]
    status_parser = auth_subparsers.add_parser(
        "status",
        help=fab_constant.COMMAND_AUTH_STATUS_DESCRIPTION,
        fab_examples=status_examples,
        fab_learnmore=["_"],
    )

    status_parser.usage = f"{utils_error_parser.get_usage_prog(status_parser)}"
    status_parser.set_defaults(func=auth.status)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(commands, custom_header=fab_constant.COMMAND_AUTH_DESCRIPTION)
