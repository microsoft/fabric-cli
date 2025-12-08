# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.utils import fab_ui


def start_interactive_mode():
    """Launch interactive mode using global parser instances"""
    try:
        from fabric_cli.core.fab_parser_setup import get_global_parser_and_subparsers
        from fabric_cli.core.fab_interactive import InteractiveCLI
        
        parser, subparsers = get_global_parser_and_subparsers()
        interactive_cli = InteractiveCLI(parser, subparsers)
        interactive_cli.start_interactive()
        
    except (KeyboardInterrupt, EOFError):
        fab_ui.print("Interactive mode cancelled.")
    except Exception as e:
        fab_ui.print(f"Failed to start interactive mode: {str(e)}")
        fab_ui.print("Please restart the CLI to use interactive mode.")