# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse


def add_global_flags(
    parser: argparse.ArgumentParser, *, output_format_default: str | None = None
) -> None:
    """
    Add global flags that apply to all commands.

    Args:
        parser: The argparse parser to add flags to.
        output_format_default: Default format, or argparse.SUPPRESS for subparsers.
    """
    # Add help flag
    parser.add_argument("-help", action="help")

    # Add format flag to override output format
    parser.add_argument(
        "--output_format",
        required=False,
        choices=["json", "text"],
        default=output_format_default,
        help="Override output format type. Optional",
    )
    parser.add_argument(
        "--json",
        dest="output_format",
        action="store_const",
        const="json",
        default=argparse.SUPPRESS,
        help="Use JSON output (same as --output_format json)",
    )

    parser.add_argument(
        "--skill",
        required=False,
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
