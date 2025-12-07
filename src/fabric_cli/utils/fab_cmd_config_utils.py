# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from fabric_cli.utils import fab_ui


def start_interactive_mode(parser=None, subparsers=None):
    """Launch interactive mode with shared parser context"""
    try:
        # Create parsers if not provided
        if parser is None or subparsers is None:
            from fabric_cli.core.fab_parser_setup import create_parser_and_subparsers
            parser, subparsers = create_parser_and_subparsers()
        
        from fabric_cli.core.fab_interactive import InteractiveCLI
        interactive_cli = InteractiveCLI(parser, subparsers)
        interactive_cli.start_interactive()
        
    except (KeyboardInterrupt, EOFError):
        fab_ui.print("Interactive mode cancelled.")
    except Exception as e:
        fab_ui.print(f"Failed to start interactive mode: {str(e)}")
        fab_ui.print("Please restart the CLI to use interactive mode.")