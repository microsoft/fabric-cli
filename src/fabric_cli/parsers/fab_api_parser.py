# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import _SubParsersAction

from fabric_cli.commands.api import fab_api as api
from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser


def register_parser(subparsers: _SubParsersAction) -> None:
    api_examples = [
        "# get workspaces",
        f"$ api -X get workspaces\n",
        "# show workspaces with headers",
        "$ api -X get workspaces --show_headers",
    ]

    api_parser = subparsers.add_parser(
        "api",
        help=fab_constant.COMMAND_API_DESCRIPTION,
        fab_examples=api_examples,
        fab_learnmore=["_"],
    )
    api_parser.add_argument("endpoint", metavar="<endpoint>", help="API endpoint URI")
    api_parser.add_argument(
        "-X",
        "--method",
        required=False,
        default="get",
        metavar="",
        choices=["get", "post", "delete", "put", "patch"],
        help="HTTP method (get, post, post, delete, put, patch). Optional, default: get",
    )
    api_parser.add_argument(
        "-i", "--input", nargs="+", default=None, help="Request body (if applicable)"
    )
    api_parser.add_argument(
        "-A",
        "--audience",
        required=False,
        default=None,
        metavar="",
        choices=["fabric", "storage", "azure", "powerbi"],
        help="Audience for token (fabric, storage, azure, powerbi). Optional, default: fabric",
    )
    api_parser.add_argument(
        "-P",
        "--params",
        metavar="",
        nargs="+",
        help="Query parameters in key=value format, separated by commas. Optional",
    )
    api_parser.add_argument(
        "-H",
        "--headers",
        metavar="",
        nargs="+",
        help="Additional headers in key=value format, separated by commas. Optional",
    )
    api_parser.add_argument(
        "-q",
        "--query",
        metavar="",
        nargs="+",
        required=False,
        help="JMESPath query to filter. Optional",
    )
    api_parser.add_argument(
        "--show_headers",
        action="store_true",
        help="Include headers in output. Optional",
    )

    api_parser.usage = f"{utils_error_parser.get_usage_prog(api_parser)}"
    api_parser.set_defaults(func=api.request_command)
