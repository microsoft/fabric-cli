# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import sys
from contextvars import ContextVar
from functools import partial
from typing import Any

import argcomplete

from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_help import CustomHelpFormatter, HelpRequest, child_parsers
from fabric_cli.parsers import fab_acls_parser as acls_parser
from fabric_cli.parsers import fab_api_parser as api_parser
from fabric_cli.parsers import fab_auth_parser as auth_parser
from fabric_cli.parsers import fab_config_parser as config_parser
from fabric_cli.parsers import fab_describe_parser as describe_parser
from fabric_cli.parsers import fab_extension_parser as extension_parser
from fabric_cli.parsers import fab_find_parser as find_parser
from fabric_cli.parsers import fab_fs_parser as fs_parser
from fabric_cli.parsers import fab_global_params
from fabric_cli.parsers import fab_jobs_parser as jobs_parser
from fabric_cli.parsers import fab_labels_parser as labels_parser
from fabric_cli.parsers import fab_tables_parser as tables_parser
from fabric_cli.utils import fab_error_parser as utils_error_parser
from fabric_cli.utils import fab_ui
from fabric_cli.utils.fab_commands import COMMANDS

_help_tokens: ContextVar[tuple[str, ...]] = ContextVar("help_tokens", default=())


class CustomArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        *args,
        fab_examples=None,
        fab_aliases=None,
        fab_learnmore=None,
        fab_notes=None,
        output_format_default: str | None = None,
        **kwargs,
    ):
        kwargs["formatter_class"] = lambda prog: CustomHelpFormatter(
            prog,
            fab_examples=fab_examples,
            fab_aliases=fab_aliases,
            fab_learnmore=fab_learnmore,
        )
        super().__init__(*args, **kwargs)
        # Add custom help and format flags
        fab_global_params.add_global_flags(
            self, output_format_default=output_format_default
        )
        self.fab_mode = fab_constant.FAB_MODE_COMMANDLINE
        self.fab_examples = fab_examples or []
        self.fab_aliases = fab_aliases or []
        self.fab_learnmore = fab_learnmore or []
        self.fab_notes = fab_notes or []

    def add_subparsers(self, **kwargs: Any) -> argparse._SubParsersAction:
        """Keep child defaults from overwriting an explicit output format."""
        kwargs.setdefault(
            "parser_class",
            partial(type(self), output_format_default=argparse.SUPPRESS),
        )
        return super().add_subparsers(**kwargs)

    def parse_args(self, args=None, namespace=None):
        tokens = list(sys.argv[1:] if args is None else args)
        context = _help_tokens.set(tuple(tokens))
        try:
            parsed = super().parse_args(tokens, namespace)
        finally:
            _help_tokens.reset(context)
        if not hasattr(parsed, "output_format"):
            setattr(parsed, "output_format", None)
        return parsed

    def print_help(self, file: Any = None) -> None:
        formats = argparse.ArgumentParser(
            add_help=False, exit_on_error=False, allow_abbrev=False
        )
        formats.add_argument("--output_format", action="append")
        formats.add_argument(
            "--json", dest="output_format", action="append_const", const="json"
        )
        args = argparse.Namespace(output_format=[])
        error = None
        try:
            formats.parse_known_args(_help_tokens.get(), args)
        except argparse.ArgumentError as exc:
            error = str(exc)
        exit_code = fab_ui.print_help(HelpRequest(self, args.output_format, error))
        if exit_code:
            self.exit(exit_code)

    def print_text_help(self):
        command_name = self.prog.split()[-1]

        help_functions = {
            "acl": lambda: acls_parser.show_help(argparse.Namespace()),
            "job": lambda: jobs_parser.show_help(argparse.Namespace()),
            "label": lambda: labels_parser.show_help(argparse.Namespace()),
            "table": lambda: tables_parser.show_help(argparse.Namespace()),
            "auth": lambda: auth_parser.show_help(argparse.Namespace()),
            "config": lambda: config_parser.show_help(argparse.Namespace()),
            "fab": lambda: fab_ui.display_help(
                COMMANDS,
                custom_header=(
                    "Usage: <command> <subcommand> [flags]"
                    if self.fab_mode == fab_constant.FAB_MODE_INTERACTIVE
                    else None
                ),
            ),
        }

        if command_name in help_functions:
            help_functions[command_name]()
        else:
            super().print_help()

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
    parser = CustomArgumentParser(
        prog="fab", description="Work seamlessly with Fabric from the command line."
    )

    # -c option for command line execution
    parser.add_argument(
        "-c",
        "--command",
        action="append",  # Allow multiple -c options
        help="Run commands in non-interactive mode",
    )

    # -version and --version
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show installed CLI version."
    )

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
    fs_parser.register_bulk_export_parser(subparsers)  # bulk-export
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
    find_parser.register_parser(subparsers)  # find
    extension_parser.register_parser(subparsers)  # extension

    # version
    version_parser = subparsers.add_parser(
        "version", help=fab_constant.COMMAND_VERSION_DESCRIPTION
    )
    version_parser.set_defaults(func=fab_ui.print_version)

    def retain_help_metadata(parent: argparse.ArgumentParser) -> None:
        for _, child, aliases, description in child_parsers(parent):
            setattr(child, "fab_description", description)
            setattr(child, "fab_aliases", aliases)
            retain_help_metadata(child)

    retain_help_metadata(parser)
    return parser, subparsers


def get_global_parser_and_subparsers():
    """Get singleton parser and subparsers instances"""
    global _global_parser, _global_subparsers

    if _global_parser is None:
        _global_parser, _global_subparsers = create_parser_and_subparsers()

    return _global_parser, _global_subparsers
