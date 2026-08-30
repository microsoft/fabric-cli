# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse


def add_global_flags(parser) -> None:
    """
    Add global flags that apply to all commands.

    Args:
        parser: The argparse parser to add flags to.
    """
    # Add help flag
    parser.add_argument("-help", action="help")

    # Add format flag to override output format
    parser.add_argument(
        "--output_format",
        required=False,
        choices=["json", "text"],
        help="Override output format type. Optional",
    )

    parser.add_argument(
        "--skill",
        required=False,
        default=argparse.SUPPRESS,
        help=(
            "Attribute Fabric API requests to a Fabric skill. "
            "Overrides the FABRIC_SKILL environment variable. Optional"
        ),
    )
