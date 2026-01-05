# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys

import argcomplete

from fabric_cli.commands.auth import fab_auth as login
from fabric_cli.core import fab_constant, fab_logger, fab_state_config
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_exceptions import FabricCLIError
from fabric_cli.core.fab_interactive import start_interactive_mode
from fabric_cli.core.fab_parser_setup import get_global_parser_and_subparsers
from fabric_cli.parsers import fab_auth_parser as auth_parser
from fabric_cli.utils import fab_ui
from fabric_cli.utils.fab_commands import COMMANDS


def main():
    parser, subparsers = get_global_parser_and_subparsers()
    
    argcomplete.autocomplete(parser, default_completer=None)

    args = parser.parse_args()

    try:
        fab_state_config.init_defaults()
        
        if args.command == "auth" and args.auth_command == None:
            auth_parser.show_help(args)
            return

        if args.command == "auth" and args.auth_command == "login":
            if login.init(args):
                if (
                    fab_state_config.get_config(fab_constant.FAB_MODE)
                    == fab_constant.FAB_MODE_INTERACTIVE
                ):
                    start_interactive_mode()
                    return

        if args.command == "auth" and args.auth_command == "logout":
            login.logout(args)
            return

        if args.command == "auth" and args.auth_command == "status":
            login.status(args)
            return

        last_exit_code = fab_constant.EXIT_CODE_SUCCESS

        if args.command:
            if args.command not in ["auth"]:
                fab_logger.print_log_file_path()
                parser.set_mode(fab_constant.FAB_MODE_COMMANDLINE)

                if isinstance(args.command, list):
                    commands_execs = 0
                    for index, command in enumerate(args.command):
                        command_parts = command.strip().split()
                        if command_parts:  # Ensure we have valid command parts
                            subparser = subparsers.choices[command_parts[0]]
                            subparser_args = subparser.parse_args(command_parts[1:])
                            subparser_args.command = command_parts[0]
                            last_exit_code = _execute_command(
                                subparser_args, subparsers, parser
                            )
                            commands_execs += 1
                            if index != len(args.command) - 1:
                                fab_ui.print_grey("------------------------------")
                    if commands_execs > 1:
                        fab_ui.print("\n")
                        fab_ui.print_output_format(
                            args, message=f"{len(args.command)} commands executed."
                        )
                else:
                    last_exit_code = _execute_command(args, subparsers, parser)

                if last_exit_code:
                    sys.exit(last_exit_code)
                else:
                    sys.exit(fab_constant.EXIT_CODE_SUCCESS)

        elif args.version:
            fab_ui.print_version()
        else:
            # AUTO-REPL: When no command is provided, automatically enter interactive mode
            start_interactive_mode()

    except KeyboardInterrupt:
        _handle_keyboard_interrupt(args)
    except Exception as err:
        _handle_unexpected_error(err, args)


def _handle_keyboard_interrupt(args):
    """Handle KeyboardInterrupt with proper error formatting."""
    fab_ui.print_output_error(
        FabricCLIError(
            "Operation cancelled",
            fab_constant.ERROR_OPERATION_CANCELLED,
        ),
        output_format_type=args.output_format,
    )
    sys.exit(fab_constant.EXIT_CODE_CANCELLED_OR_MISUSE_BUILTINS)


def _handle_unexpected_error(err, args):
    """Handle unexpected errors with proper error formatting."""
    try:
        error_message = str(err.args[0]) if err.args else str(err)
    except:
        error_message = "An unexpected error occurred"
    
    fab_ui.print_output_error(
        FabricCLIError(error_message, fab_constant.ERROR_UNEXPECTED_ERROR), 
        output_format_type=args.output_format,
        )
    sys.exit(fab_constant.EXIT_CODE_ERROR)


def _execute_command(args, subparsers, parser):
    if args.command in subparsers.choices:
        subparser_args = args
        subparser_args.command = args.command
        subparser_args.fab_mode = parser.get_mode()
        subparser_args.command_path = Command.get_command_path(subparser_args)

        if hasattr(subparser_args, "func"):
            return subparser_args.func(subparser_args)
        else:
            return None
    else:
        parser.error(f"invalid choice: '{args.command.strip()}'")
        return None


if __name__ == "__main__":
    main()

