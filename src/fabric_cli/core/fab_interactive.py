# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import html
import shlex

from prompt_toolkit import HTML, PromptSession
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

from fabric_cli.core import fab_constant, fab_logger
from fabric_cli.core.fab_commands import Command
from fabric_cli.core.fab_context import Context
from fabric_cli.utils import fab_commands
from fabric_cli.utils import fab_ui as utils_ui


class InteractiveCLI:
    def __init__(self, parser, subparsers):
        self.parser = parser
        self.parser.set_mode(fab_constant.FAB_MODE_INTERACTIVE)
        self.subparsers = subparsers
        self.history = InMemoryHistory()
        self.session = self.init_session(self.history)
        self.custom_style = Style(
            [
                ("prompt", "fg:#49C5B1"),  # Prompt color, original #49C5B1
                ("context", "fg:#017864"),  # Context color, original #017864
                ("detail", "fg:grey"),
                ("input", "fg:white"),  # Input color
            ]
        )

    def init_session(self, session_history: InMemoryHistory) -> PromptSession:
        return PromptSession(history=session_history)

    def handle_command(self, command):
        """Process the user command."""
        fab_logger.print_log_file_path()

        command_parts = shlex.split(command.strip())  # Split the command into parts

        # Handle special commands first
        if command in fab_constant.INTERACTIVE_QUIT_COMMANDS:
            utils_ui.print(fab_constant.INTERACTIVE_EXIT_MESSAGE)
            return True  # Exit
        elif command in fab_constant.INTERACTIVE_HELP_COMMANDS:
            utils_ui.display_help(
                fab_commands.COMMANDS, "Usage: <command> <subcommand> [flags]"
            )
            return False  # Do not exit
        elif command in fab_constant.INTERACTIVE_VERSION_COMMANDS:
            utils_ui.print_version()
            return False  # Do not exit

        # Interactive mode
        self.parser.set_mode(fab_constant.FAB_MODE_INTERACTIVE)

        # Now check for subcommands
        if command_parts:  # Only if there's something to process
            subcommand_name = command_parts[0]
            if subcommand_name in self.subparsers.choices:
                subparser = self.subparsers.choices[subcommand_name]

                try:
                    subparser_args = subparser.parse_args(command_parts[1:])
                    subparser_args.command = subcommand_name
                    subparser_args.fab_mode = fab_constant.FAB_MODE_INTERACTIVE
                    subparser_args.command_path = Command.get_command_path(
                        subparser_args
                    )

                    if not command_parts[1:]:
                        subparser_args.func(subparser_args)
                    elif hasattr(subparser_args, "func"):
                        subparser_args.func(subparser_args)
                    else:
                        utils_ui.print(
                            f"No function associated with the command: {command.strip()}"
                        )
                except SystemExit:
                    # Catch SystemExit raised by ArgumentParser and prevent exiting
                    return
            else:
                self.parser.error(f"invalid choice: '{command.strip()}'")

        return False

    def start_interactive(self):
        """Start the interactive mode using prompt_toolkit for input."""
        utils_ui.print("\nWelcome to the Fabric CLI ⚡")
        utils_ui.print("Type 'help' for help. \n")

        while True:
            try:
                context = Context().context
                pwd_context = f"/{context.path.strip('/')}"

                prompt_text = HTML(
                    f"<prompt>fab</prompt><detail>:</detail><context>{html.escape(pwd_context)}</context><detail>$</detail> "
                )

                user_input = self.session.prompt(
                    prompt_text,
                    style=self.custom_style,
                    cursor=CursorShape.BLINKING_BEAM,
                    enable_history_search=True,
                )
                should_exit = self.handle_command(user_input)
                if should_exit:  # Check if the command was to exit
                    break

            except (EOFError, KeyboardInterrupt):
                utils_ui.print(f"\n{fab_constant.INTERACTIVE_EXIT_MESSAGE}")
                break
