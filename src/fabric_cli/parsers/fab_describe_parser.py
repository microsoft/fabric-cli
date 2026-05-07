# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.core import fab_constant
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils.fab_lazy_load import lazy_command

_describe_module_path = "fabric_cli.commands.desc.fab_describe"


def register_parser(subparsers: _SubParsersAction) -> None:
    desc_examples = [
        "# check command support for .Capacity (using extension)",
        "$ desc .capacity\n",
        "# check command support for an existing capacity (using path)",
        "$ desc .capacities/capac1.Capacity\n",
        "# check command support for .Notebook (using extension)",
        "$ desc .notebook\n",
        "# check command support for an existing notebook (using path)",
        "$ desc /ws1.Workspace/nb1.Notebook",
    ]
    desc_learnmore = ["Tip: Use `desc all` to check all Dot elements"]

    describe_parser = subparsers.add_parser(
        "desc",
        help=fab_constant.COMMAND_DESCRIBE_DESCRIPTION,
        fab_examples=desc_examples,
        fab_learnmore=desc_learnmore,
    )
    describe_parser.add_argument(
        "path", nargs="*", type=str, default=None, help="Directory path"
    )
    describe_parser.usage = f"{utils_error_parser.get_usage_prog(describe_parser)}"
    describe_parser.set_defaults(
        func=lazy_command(_describe_module_path, "show_commands_supported")
    )
