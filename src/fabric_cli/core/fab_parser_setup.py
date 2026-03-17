# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import re
import sys

import argcomplete

from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.parsers import fab_acls_parser as acls_parser
from fabric_cli.parsers import fab_api_parser as api_parser
from fabric_cli.parsers import fab_auth_parser as auth_parser
from fabric_cli.parsers import fab_config_parser as config_parser
from fabric_cli.parsers import fab_describe_parser as describe_parser
from fabric_cli.parsers import fab_extension_parser as extension_parser
from fabric_cli.parsers import fab_fs_parser as fs_parser
from fabric_cli.parsers import fab_global_params
from fabric_cli.parsers import fab_jobs_parser as jobs_parser
from fabric_cli.parsers import fab_labels_parser as labels_parser
from fabric_cli.parsers import fab_tables_parser as tables_parser
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui
from fabric_cli.utils.fab_commands import COMMANDS


class CustomHelpFormatter(argparse.HelpFormatter):

    def __init__(
        self,
        prog,
        fab_examples=None,
        fab_aliases=None,
        fab_learnmore=None,
        *args,
        **kwargs,
    ):
        super().__init__(prog, *args, **kwargs)
        self.fab_examples = fab_examples or []
        self.fab_aliases = fab_aliases or []
        self.fab_learnmore = fab_learnmore or []

    def _format_args(self, action, default_metavar):
        if action.nargs in ("*", "+"):
            if action.option_strings:
                return ""
            else:
                # Ensure metavar is lowercase for positional arguments
                return f"<{action.dest}>"
        return super()._format_args(action, default_metavar)

    def _format_action_invocation(self, action):
        if not action.metavar and action.nargs in (None, "?"):
            # For no metavar and simple arguments
            return ", ".join(action.option_strings)
        elif action.nargs in ("*", "+"):
            metavar = self._format_args(action, action.dest)
            return ", ".join(action.option_strings) + metavar
        else:
            return super()._format_action_invocation(action)

    def format_help(self):
        help_message = super().format_help()

        # Custom output
        help_message = help_message.replace("usage:", "Usage:")
        help_message = help_message.replace("positional arguments:", "Arg(s):")
        help_message = help_message.replace("options:", "Flags:")

        help_message = re.sub(
            r"\s*-h, --help\s*(Show help for command|show this help message and exit)?",
            "",
            help_message,
        )
        help_message = help_message.replace("  -help\n", "")
        help_message = help_message.replace("[-h] ", "")
        help_message = help_message.replace("[-help] ", "")
        help_message = help_message.replace("[-help]", "")

        if "Flags:" in help_message:
            flags_section = help_message.split("Flags:")[1].strip()
            if not flags_section:  # If no flags follow the "Flags:" line, remove it
                help_message = help_message.replace("\nFlags:\n", "")

        # Add aliases
        if self.fab_aliases:
            help_message += "\nAliases:\n"
            for alias in self.fab_aliases:
                help_message += f"  {alias}\n"

        # Add examples
        if self.fab_examples:
            help_message += "\nExamples:\n"
            for example in self.fab_examples:
                if "#" in example:
                    # Grey color
                    help_message += f"  \033[38;5;243m{example}\033[0m\n"
                else:
                    help_message += f"  {example}\n"

        # Add learn more
        if self.fab_learnmore:
            help_message += "\nLearn more:\n"
            if self.fab_learnmore != ["_"]:
                for learn_more in self.fab_learnmore:
                    help_message += f"  {learn_more}\n"
            help_message += "  For more usage examples, see https://aka.ms/fabric-cli\n"

        return help_message + "\n"


class CustomArgumentParser(argparse.ArgumentParser):
    def __init__(
        self, *args, fab_examples=None, fab_aliases=None, fab_learnmore=None, **kwargs
    ):
        kwargs["formatter_class"] = lambda prog: CustomHelpFormatter(
            prog,
            fab_examples=fab_examples,
            fab_aliases=fab_aliases,
            fab_learnmore=fab_learnmore,
        )
        super().__init__(*args, **kwargs)
        # Add custom help and format flags
        fab_global_params.add_global_flags(self)
        self.fab_mode = fab_constant.FAB_MODE_COMMANDLINE
        self.fab_examples = fab_examples or []
        self.fab_aliases = fab_aliases or []

    def print_help(self, file=None):
        command_name = self.prog.split()[-1]

        help_functions = {
            "acl": lambda: acls_parser.show_help(None),
            "job": lambda: jobs_parser.show_help(None),
            "label": lambda: labels_parser.show_help(None),
            "table": lambda: tables_parser.show_help(None),
            "auth": lambda: auth_parser.show_help(None),
            "config": lambda: config_parser.show_help(None),
            "fab": lambda: fab_ui.display_help(COMMANDS),
        }

        if command_name in help_functions:
            help_functions[command_name]()
        else:
            super().print_help(file)

    def set_mode(self, mode):
        self.fab_mode = mode

    def get_mode(self):
        return self.fab_mode

    def error(self, message):
        if "invalid choice" in message:
            utils_error_parser.invalid_choice(self, message)
        elif "unrecognized arguments" in message:
            utils_error_parser.unrecognized_arguments(message)
        elif "the following arguments are required" in message:
            utils_error_parser.missing_required_arguments(message)
        else:
            # Add more custom error parsers here
            fab_logger.log_warning(message)

        if self.fab_mode == fab_constant.FAB_MODE_COMMANDLINE:
            sys.exit(2)


# Global parser instances
_global_parser = None
_global_subparsers = None

def create_parser_and_subparsers():
    """Create parser and subparsers for reuse across CLI modes"""
    parser = CustomArgumentParser(description="Fabric CLI")

    # -c option for command line execution
    parser.add_argument(
        "-c",
        "--command",
        action="append",  # Allow multiple -c options
        help="Run commands in non-interactive mode",
    )

    # -version and --version
    parser.add_argument("-v", "--version", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=False)

    # Custom parsers
    config_parser.register_parser(subparsers)

    # Single parsers
    fs_parser.register_ls_parser(subparsers)  # ls
    fs_parser.register_mkdir_parser(subparsers)  # mkdir
    fs_parser.register_cd_parser(subparsers)  # cd
    fs_parser.register_rm_parser(subparsers)  # rm
    fs_parser.register_mv_parser(subparsers)  # mv
    fs_parser.register_cp_parser(subparsers)  # cp
    fs_parser.register_exists_parser(subparsers)  # exists
    fs_parser.register_pwd_parser(subparsers)  # pwd
    fs_parser.register_open_parser(subparsers)  # open
    fs_parser.register_export_parser(subparsers)  # export
    fs_parser.register_import_parser(subparsers)  # import
    fs_parser.register_deploy_parser(subparsers)  # deploy
    fs_parser.register_set_parser(subparsers)  # set
    fs_parser.register_get_parser(subparsers)  # get
    fs_parser.register_clear_parser(subparsers)  # clear
    fs_parser.register_ln_parser(subparsers)  # ln
    fs_parser.register_start_parser(subparsers)  # start
    fs_parser.register_stop_parser(subparsers)  # stop
    fs_parser.register_assign_parser(subparsers)  # assign
    fs_parser.register_unassign_parser(subparsers)  # unassign

    jobs_parser.register_parser(subparsers)  # jobs
    tables_parser.register_parser(subparsers)  # tables
    acls_parser.register_parser(subparsers)  # acls
    labels_parser.register_parser(subparsers)  # labels

    api_parser.register_parser(subparsers)  # api
    auth_parser.register_parser(subparsers)  # auth
    describe_parser.register_parser(subparsers)  # desc
    extension_parser.register_parser(subparsers)  # extension

    # version
    version_parser = subparsers.add_parser(
        "version", help=fab_constant.COMMAND_VERSION_DESCRIPTION
    )
    version_parser.set_defaults(func=fab_ui.print_version)

    return parser, subparsers

def get_global_parser_and_subparsers():
    """Get singleton parser and subparsers instances"""
    global _global_parser, _global_subparsers
    
    if _global_parser is None:
        _global_parser, _global_subparsers = create_parser_and_subparsers()
    
    return _global_parser, _global_subparsers

