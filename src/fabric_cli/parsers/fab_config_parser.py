# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from argparse import Namespace, _SubParsersAction

from fabric_cli.commands.config import fab_config as config
from fabric_cli.core import fab_constant
from fabric_cli.core.completers import fab_config_completers
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui as utils_ui
from fabric_cli.utils.fab_util import get_os_specific_command

commands = {
    "Commands": {
        "clear-cache": "Clear the CLI cache.",
        "get": "Print the value of a given configuration key.",
        get_os_specific_command("ls"): "List all configuration keys and their values.",
        "set": "Set a configuration key to a specified value.",
    }
}


def register_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "config", help=fab_constant.COMMAND_CONFIG_DESCRIPTION
    )
    parser.set_defaults(func=show_help)
    config_subparsers = parser.add_subparsers(dest="config_subcommand")

    # Subcommand for 'set'
    set_examples = [
        "# switch to command line mode",
        "$ config set mode command_line\n",
        "# set default capacity",
        "$ config set default_capacity Trial-0000",
    ]

    parser_set = config_subparsers.add_parser(
        "set",
        help="Set a configuration value",
        fab_examples=set_examples,
        fab_learnmore=["_"],
    )

    set_key_arg = parser_set.add_argument(
        "key", metavar="<key>", help="Configuration key"
    )
    set_key_arg.completer = fab_config_completers.complete_config_keys

    set_value_arg = parser_set.add_argument(
        "value", metavar="<value>", help="Configuration value"
    )
    set_value_arg.completer = fab_config_completers.complete_config_values

    parser_set.usage = f"{utils_error_parser.get_usage_prog(parser_set)}"
    parser_set.set_defaults(func=config.set_config)

    # Subcommand for 'get'
    get_examples = [
        "# get current CLI mode",
        "$ config get mode\n",
        "# get default capacity",
        "$ config get default_capacity",
    ]

    parser_get = config_subparsers.add_parser(
        "get",
        help="Get a configuration value",
        fab_examples=get_examples,
        fab_learnmore=["_"],
    )

    # Add completer to key argument
    get_key_arg = parser_get.add_argument(
        "key", metavar="<key>", help="Configuration key"
    )
    get_key_arg.completer = fab_config_completers.complete_config_keys

    parser_get.usage = f"{utils_error_parser.get_usage_prog(parser_get)}"
    parser_get.set_defaults(func=config.get_config)

    # Subcommand for 'ls'
    ls_examples = ["# print configuration values", "$ config ls"]

    parser_ls = config_subparsers.add_parser(
        "ls",
        help="List all configuration values",
        aliases=["dir"],
        fab_examples=ls_examples,
        fab_learnmore=["_"],
    )

    parser_ls.add_argument(
        "-q",
        "--query",
        metavar="",
        nargs="+",
        required=False,
        help="JMESPath query to filter. Optional",
    )

    parser_ls.usage = f"{utils_error_parser.get_usage_prog(parser_ls)}"
    parser_ls.set_defaults(func=config.list_configs)

    clearcache_examples = ["# clear CLI cache", "$ config clear-cache"]

    parser_clear_cache = config_subparsers.add_parser(
        "clear-cache",
        help="Clear cache",
        fab_examples=clearcache_examples,
        fab_learnmore=["_"],
    )

    parser_clear_cache.usage = (
        f"{utils_error_parser.get_usage_prog(parser_clear_cache)}"
    )
    parser_clear_cache.set_defaults(func=config.clear_cache)


def show_help(args: Namespace) -> None:
    utils_ui.display_help(
        commands, custom_header=fab_constant.COMMAND_CONFIG_DESCRIPTION
    )
